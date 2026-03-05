from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Pass
from accounts.models import CustomUser

@login_required
def pass_list_view(request):
    """Display passes for the current user's location only"""
    # Strict location filtering - only show passes from user's location
    passes = Pass.objects.filter(location=request.user.assigned_location).order('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        passes = passes.filter(
            Q(visitor_name__icontains=search_query) |
            Q(pass_number__icontains=search_query) |
            Q(purpose__icontains=search_query) |
            Q(host_name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        passes = passes.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(passes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_passes': passes.count(),
        'active_passes': passes.filter(status='active').count(),
        'completed_passes': passes.filter(status='completed').count(),
    }
    return render(request, 'reception/pass_list.html', context)

@login_required
def pass_create_view(request):
    """Create a new pass - automatically inherits user's location"""
    if request.method == 'POST':
        # Create pass with automatic location inheritance
        pass_obj = Pass(
            visitor_name=request.POST.get('visitor_name'),
            visitor_email=request.POST.get('visitor_email', ''),
            visitor_phone=request.POST.get('visitor_phone', ''),
            visitor_type=request.POST.get('visitor_type', 'guest'),
            company_name=request.POST.get('company_name', ''),
            purpose=request.POST.get('purpose'),
            host_name=request.POST.get('host_name'),
            host_department=request.POST.get('host_department', ''),
            expected_departure=request.POST.get('expected_departure'),
            notes=request.POST.get('notes', ''),
            location=request.user.assigned_location,  # Auto-inherit location
            created_by=request.user
        )
        
        try:
            pass_obj.save()
            messages.success(request, f'Pass #{pass_obj.pass_number} created successfully!')
            return redirect('reception:pass_detail', pk=pass_obj.pk)
        except Exception as e:
            messages.error(request, f'Error creating pass: {str(e)}')
    
    return render(request, 'reception/pass_form.html', {
        'title': 'Create New Pass',
        'action': 'Create'
    })

@login_required
def pass_detail_view(request, pk):
    """View pass details - enforce location-based access control"""
    pass_obj = get_object_or_404(Pass, pk=pk)
    
    # CRITICAL: Enforce location-based access control
    if pass_obj.location != request.user.assigned_location:
        messages.error(request, 'Access denied. You can only view passes from your location.')
        return redirect('reception:pass_list')
    
    context = {
        'pass': pass_obj,
        'can_edit': request.user.role in ['admin', 'receptionist'],
    }
    return render(request, 'reception/pass_detail.html', context)

@login_required
def pass_update_view(request, pk):
    """Update pass details - enforce location-based access control"""
    pass_obj = get_object_or_404(Pass, pk=pk)
    
    # CRITICAL: Enforce location-based access control
    if pass_obj.location != request.user.assigned_location:
        messages.error(request, 'Access denied. You can only edit passes from your location.')
        return redirect('reception:pass_list')
    
    # Only admins and receptionists can edit passes
    if request.user.role not in ['admin', 'receptionist']:
        messages.error(request, 'You do not have permission to edit passes.')
        return redirect('reception:pass_list')
    
    if request.method == 'POST':
        pass_obj.visitor_name = request.POST.get('visitor_name')
        pass_obj.visitor_email = request.POST.get('visitor_email', '')
        pass_obj.visitor_phone = request.POST.get('visitor_phone', '')
        pass_obj.visitor_type = request.POST.get('visitor_type', 'guest')
        pass_obj.company_name = request.POST.get('company_name', '')
        pass_obj.purpose = request.POST.get('purpose')
        pass_obj.host_name = request.POST.get('host_name')
        pass_obj.host_department = request.POST.get('host_department', '')
        pass_obj.expected_departure = request.POST.get('expected_departure')
        pass_obj.notes = request.POST.get('notes', '')
        
        try:
            pass_obj.save()
            messages.success(request, f'Pass #{pass_obj.pass_number} updated successfully!')
            return redirect('reception:pass_detail', pk=pass_obj.pk)
        except Exception as e:
            messages.error(request, f'Error updating pass: {str(e)}')
    
    return render(request, 'reception/pass_form.html', {
        'pass': pass_obj,
        'title': 'Update Pass',
        'action': 'Update'
    })

@login_required
def pass_checkout_view(request, pk):
    """Check out a visitor - enforce location-based access control"""
    pass_obj = get_object_or_404(Pass, pk=pk)
    
    # CRITICAL: Enforce location-based access control
    if pass_obj.location != request.user.assigned_location:
        messages.error(request, 'Access denied. You can only check out passes from your location.')
        return redirect('reception:pass_list')
    
    # Only admins and receptionists can check out passes
    if request.user.role not in ['admin', 'receptionist']:
        messages.error(request, 'You do not have permission to check out passes.')
        return redirect('reception:pass_list')
    
    if request.method == 'POST':
        if pass_obj.status == 'active':
            from django.utils import timezone
            pass_obj.check_out_time = timezone.now()
            pass_obj.status = 'completed'
            pass_obj.save()
            messages.success(request, f'Pass #{pass_obj.pass_number} checked out successfully!')
        else:
            messages.warning(request, f'Pass #{pass_obj.pass_number} is already checked out.')
        
        return redirect('reception:pass_detail', pk=pass_obj.pk)
    
    return render(request, 'reception/pass_confirm_checkout.html', {'pass': pass_obj})
