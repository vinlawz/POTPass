from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, Min, Max, F, ExpressionWrapper
from django.db.models.functions import Extract, ExtractDay
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from .models import Visitor, Visit, AuditLog
from .forms import (
    VisitorForm, VisitForm, VisitorSearchForm, 
    VisitFilterForm, CheckInForm, CheckOutForm
)
from .signals import get_client_ip
from core.models import Location

def log_action(user, action, visit=None, visitor=None, notes=None):
    """Helper function to log audit actions"""
    AuditLog.objects.create(
        user=user,
        action=action,
        visit=visit,
        visitor=visitor,
        notes=notes,
        ip_address=get_client_ip(None)  # Will be implemented in signals
    )

@login_required
def visitor_register_view(request):
    """Handle visitor registration with comprehensive information"""
    if request.method == 'POST':
        form = VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save()
            
            # Log action
            log_action(
                user=request.user,
                action='CREATE_VISITOR',
                visitor=visitor
            )
            
            messages.success(
                request, 
                f'Visitor {visitor.full_name} registered successfully!'
            )
            
            # Check if we should create a visit immediately
            create_visit = request.POST.get('create_visit', False)
            if create_visit:
                return redirect('visitor:visit_create', visitor_id=visitor.pk)
            else:
                return redirect('visitor:visitor_list')
    else:
        form = VisitorForm()
    
    return render(request, 'visitor/visitor_register.html', {
        'form': form,
        'title': 'Register New Visitor'
    })

@login_required
def dashboard_view(request):
    """Main visitor management dashboard"""
    # Dashboard indicators
    active_visits = Visit.objects.filter(
        location=request.user.assigned_location,
        status='ACTIVE'
    )
    
    today = timezone.now().date()
    today_visits = Visit.objects.filter(
        location=request.user.assigned_location,
        check_in_time__date=today
    )
    
    this_month = timezone.now().replace(day=1).date()
    month_visits = Visit.objects.filter(
        location=request.user.assigned_location,
        check_in_time__date__gte=this_month
    )
    
    # Recent check-ins
    recent_checkins = Visit.objects.filter(
        location=request.user.assigned_location
    ).order_by('-check_in_time')[:5]
    
    context = {
        'active_visitors_count': active_visits.count(),
        'today_visits_count': today_visits.count(),
        'month_visits_count': month_visits.count(),
        'recent_checkins': recent_checkins,
        'active_visits': active_visits,
    }
    return render(request, 'visitor/dashboard.html', context)

@login_required
def check_in_view(request):
    """Handle visitor check-in process"""
    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            
            # Search for visitor by phone or ID
            visitor = None
            try:
                # Try phone first
                visitor = Visitor.objects.get(
                    Q(phone__icontains=search_query) |
                    Q(id_number__icontains=search_query)
                )
            except Visitor.DoesNotExist:
                # Create new visitor if not found
                return redirect('visitor:visitor_create', search=search_query)
            
            # Check for active visit
            active_visit = visitor.visits.filter(
                location=request.user.assigned_location,
                status='ACTIVE'
            ).first()
            
            if active_visit:
                messages.warning(
                    request, 
                    f'{visitor.full_name} already has an active visit.'
                )
                return redirect('visitor:visit_detail', pk=active_visit.pk)
            
            # Create new visit
            visit = Visit.objects.create(
                visitor=visitor,
                location=request.user.assigned_location,
                check_in_time=timezone.now(),
                status='ACTIVE',
                created_by=request.user
            )
            
            # Log action
            log_action(
                user=request.user,
                action='CHECK_IN',
                visit=visit,
                visitor=visitor
            )
            
            messages.success(
                request, 
                f'Check-in successful for {visitor.full_name}!'
            )
            
            return redirect('visitor:visit_detail', pk=visit.pk)
    else:
        form = CheckInForm()
    
    return render(request, 'visitor/check_in.html', {'form': form})

@login_required
def check_out_view(request, pk):
    """Handle visitor check-out process"""
    visit = get_object_or_404(Visit, pk=pk)
    
    # Security check
    if visit.location != request.user.assigned_location:
        messages.error(request, 'Access denied. You can only check out visitors from your location.')
        return redirect('visitor:dashboard')
    
    if visit.status != 'ACTIVE':
        messages.warning(request, 'This visit is already completed.')
        return redirect('visitor:visit_detail', pk=pk)
    
    if request.method == 'POST':
        form = CheckOutForm(request.POST)
        if form.is_valid():
            # Perform check-out
            visit.check_out()
            
            # Log action
            log_action(
                user=request.user,
                action='CHECK_OUT',
                visit=visit,
                visitor=visit.visitor,
                notes=form.cleaned_data.get('notes', '')
            )
            
            messages.success(
                request, 
                f'Check-out successful for {visit.visitor.full_name}!'
            )
            
            return redirect('visitor:visit_detail', pk=pk)
    else:
        form = CheckOutForm()
    
    return render(request, 'visitor/check_out.html', {
        'visit': visit,
        'form': form
    })

@login_required
def visitor_create_view(request):
    """Create a new visitor"""
    search_query = request.GET.get('search', '')
    
    if request.method == 'POST':
        form = VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save()
            
            # Log action
            log_action(
                user=request.user,
                action='CREATE_VISITOR',
                visitor=visitor
            )
            
            messages.success(
                request, 
                f'Visitor {visitor.full_name} created successfully!'
            )
            
            # Redirect to create visit
            return redirect('visitor:visit_create', visitor_id=visitor.pk)
    else:
        form = VisitorForm(initial={'phone': search_query if search_query else None})
    
    return render(request, 'visitor/visitor_form.html', {
        'form': form,
        'title': 'Create New Visitor',
        'search_query': search_query
    })
@login_required
def visitor_list_view(request):
    """List and search visitors"""
    form = VisitorSearchForm(request.GET)
    visitors = Visitor.objects.filter(
        visits__location=request.user.assigned_location
    ).distinct()
    
    if form.is_valid():
        search_type = form.cleaned_data['search_type']
        query = form.cleaned_data['query']
        
        if search_type == 'name':
            visitors = visitors.filter(full_name__icontains=query)
        elif search_type == 'phone':
            visitors = visitors.filter(phone__icontains=query)
        elif search_type == 'id_number':
            visitors = visitors.filter(id_number__icontains=query)
    
    # Add annotations for visitor statistics
    from django.db.models import Count, Q, Avg, F
    from django.db.models.functions import Cast
    visitors = visitors.annotate(
        total_visits=Count('visits', filter=Q(visits__location=request.user.assigned_location))
    ).order_by('-total_visits')
    
    # Get last visit for each visitor
    for visitor in visitors:
        last_visit = visitor.visits.filter(
            location=request.user.assigned_location
        ).order_by('-check_in_time').first()
        visitor.last_visit = last_visit.check_in_time if last_visit else None
    
    # Pagination
    paginator = Paginator(visitors, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'visitor/visitor_list.html', {
        'form': form,
        'page_obj': page_obj,
        'total_visitors': visitors.count(),
    })

@login_required
def visit_create_view(request, visitor_id=None):
    """Create a new visit"""
    visitor = None
    if visitor_id:
        visitor = get_object_or_404(Visitor, pk=visitor_id)
    
    if request.method == 'POST':
        form = VisitForm(request.POST, location=request.user.assigned_location)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.location = request.user.assigned_location
            visit.check_in_time = timezone.now()
            visit.status = 'ACTIVE'
            visit.created_by = request.user
            visit.save()
            
            # Log action
            log_action(
                user=request.user,
                action='CHECK_IN',
                visit=visit,
                visitor=visitor
            )
            
            messages.success(
                request, 
                f'Visit created for {visit.visitor.full_name}!'
            )
            
            return redirect('visitor:visit_detail', pk=visit.pk)
    else:
        form = VisitForm(
            location=request.user.assigned_location,
            initial={'visitor': visitor} if visitor else None
        )
    
    return render(request, 'visitor/visit_form.html', {
        'form': form,
        'visitor': visitor,
        'title': 'Create New Visit'
    })

@login_required
def visit_list_view(request):
    """List and filter visits"""
    form = VisitFilterForm(request.GET)
    visits = Visit.objects.filter(location=request.user.assigned_location)
    
    if form.is_valid():
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if status:
            visits = visits.filter(status=status)
        if date_from:
            visits = visits.filter(check_in_time__date__gte=date_from)
        if date_to:
            visits = visits.filter(check_in_time__date__lte=date_to)
    
    # Default view: Today's visits, active on top
    today = timezone.now().date()
    if not any([status, date_from, date_to]):
        visits = visits.filter(check_in_time__date=today)
        visits = visits.order_by('-status', '-check_in_time')
    
    # Pagination
    paginator = Paginator(visits, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_visits = visits.count()
    active_visits = visits.filter(status='ACTIVE').count()
    completed_visits = visits.filter(status='COMPLETED').count()
    cancelled_visits = visits.filter(status='CANCELLED').count()
    
    return render(request, 'visitor/visit_list.html', {
        'form': form,
        'page_obj': page_obj,
        'total_visits': total_visits,
        'active_visits': active_visits,
        'completed_visits': completed_visits,
        'cancelled_visits': cancelled_visits,
    })

@login_required
def visit_detail_view(request, pk):
    """View visit details"""
    visit = get_object_or_404(Visit, pk=pk)
    
    # Security check
    if visit.location != request.user.assigned_location:
        messages.error(request, 'Access denied. You can only view visits from your location.')
        return redirect('visitor:dashboard')
    
    return render(request, 'visitor/visit_detail.html', {'visit': visit})

@login_required
def reports_view(request):
    """Main reports dashboard with analytics and filtering"""
    # Get base queryset with location filtering
    base_visits = Visit.objects.filter(location=request.user.assigned_location)
    
    # Handle filtering
    form = VisitFilterForm(request.GET)
    visits = base_visits
    
    if form.is_valid():
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if status:
            visits = visits.filter(status=status)
        if date_from:
            visits = visits.filter(check_in_time__date__gte=date_from)
        if date_to:
            visits = visits.filter(check_in_time__date__lte=date_to)
    
    # Calculate statistics
    total_visits = visits.count()
    active_visits = visits.filter(status='ACTIVE').count()
    completed_visits = visits.filter(status='COMPLETED').count()
    
    # Average visit duration
    completed_with_duration = visits.filter(
        status='COMPLETED',
        check_out_time__isnull=False
    )
    
    # Calculate average duration in minutes using raw SQL
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT AVG(
                (julianday(check_out_time) - julianday(check_in_time)) * 24 * 60
            ) as avg_duration_minutes
            FROM visitor_visit 
            WHERE status = 'COMPLETED' 
            AND check_out_time IS NOT NULL
            AND location_id = %s
        """, [request.user.assigned_location.id])
        result = cursor.fetchone()
        avg_duration_minutes = result[0] if result and result[0] is not None else 0
    
    # Peak hours analysis
    from django.db.models.functions import ExtractHour
    peak_hour_data = visits.annotate(
        hour=ExtractHour('check_in_time')
    ).values('hour').annotate(
        visit_count=Count('id')
    ).order_by('-visit_count')[:5]
    
    # Recent activity
    recent_visits = visits.order_by('-check_in_time')[:10]
    
    # Pagination
    paginator = Paginator(visits, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_visits': total_visits,
        'active_visits': active_visits,
        'completed_visits': completed_visits,
        'avg_duration_minutes': round(avg_duration_minutes, 1),
        'peak_hours': peak_hour_data,
        'recent_visits': recent_visits,
    }
    return render(request, 'visitor/reports.html', context)

@login_required
def export_visits_view(request):
    """Export visits to CSV"""
    # Get filtered visits
    base_visits = Visit.objects.filter(location=request.user.assigned_location)
    
    # Apply same filters as reports
    form = VisitFilterForm(request.GET)
    visits = base_visits
    
    if form.is_valid():
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if status:
            visits = visits.filter(status=status)
        if date_from:
            visits = visits.filter(check_in_time__date__gte=date_from)
        if date_to:
            visits = visits.filter(check_in_time__date__lte=date_to)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="visits_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'Pass Number', 'Visitor Name', 'Phone', 'Organization', 'Purpose', 
        'Host', 'Check-In Time', 'Check-Out Time', 'Duration', 'Status'
    ])
    
    # Data rows
    for visit in visits:
        duration = ''
        if visit.check_out_time:
            duration_minutes = int((visit.check_out_time - visit.check_in_time).total_seconds() / 60)
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            if hours > 0:
                duration = f"{hours}h {minutes}m"
            else:
                duration = f"{minutes}m"
        
        writer.writerow([
            f"V{visit.pk:06d}",
            visit.visitor.full_name,
            visit.visitor.phone,
            visit.visitor.organization or '',
            visit.purpose,
            visit.host or '',
            visit.check_in_time.strftime('%Y-%m-%d %H:%M'),
            visit.check_out_time.strftime('%Y-%m-%d %H:%M') if visit.check_out_time else '',
            duration,
            visit.get_status_display()
        ])
    
    return response

@login_required
def daily_summary_view(request):
    """Daily summary with printable badges"""
    # Get today's visits
    today = timezone.now().date()
    visits = Visit.objects.filter(
        location=request.user.assigned_location,
        check_in_time__date=today
    ).order_by('-check_in_time')
    
    # Group by status
    active_visits = [v for v in visits if v.status == 'ACTIVE']
    completed_visits = [v for v in visits if v.status == 'COMPLETED']
    
    context = {
        'today': today,
        'visits': visits,
        'active_visits': active_visits,
        'completed_visits': completed_visits,
        'total_count': len(visits),
        'active_count': len(active_visits),
        'completed_count': len(completed_visits),
    }
    return render(request, 'visitor/daily_summary.html', context)

@require_POST
@login_required
def bulk_check_in_view(request):
    """Bulk check-in for multiple visitors"""
    visitor_data = request.POST.getlist('visitor_data')
    checked_in_visitors = []
    errors = []
    
    for data in visitor_data:
        try:
            visitor_id = data.get('visitor_id')
            purpose = data.get('purpose', '')
            host = data.get('host', '')
            
            if not visitor_id:
                errors.append(f'Row {len(checked_in_visitors) + 1}: Missing visitor ID')
                continue
            
            visitor = Visitor.objects.get(id=visitor_id)
            
            # Check for active visit
            active_visit = visitor.visits.filter(
                location=request.user.assigned_location,
                status='ACTIVE'
            ).first()
            
            if active_visit:
                errors.append(f'Visitor {visitor.full_name} already has an active visit')
                continue
            
            # Create new visit
            visit = Visit.objects.create(
                visitor=visitor,
                location=request.user.assigned_location,
                purpose=purpose,
                host=host,
                check_in_time=timezone.now(),
                status='ACTIVE',
                created_by=request.user
            )
            
            # Log action
            log_action(
                user=request.user,
                action='CHECK_IN',
                visit=visit,
                visitor=visitor
            )
            
            checked_in_visitors.append(visit)
            
        except Exception as e:
            errors.append(f'Error processing visitor {data.get("visitor_id", "unknown")}: {str(e)}')
    
    if errors:
        for error in errors:
            messages.error(request, error)
    else:
        messages.success(request, f'Successfully checked in {len(checked_in_visitors)} visitors')
    
    context = {
        'checked_in_visitors': checked_in_visitors,
        'errors': errors,
    }
    return render(request, 'visitor/bulk_check_in.html', context)

@login_required
def visitor_search_ajax(request):
    """Enhanced AJAX search with more details"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Search visitors by multiple fields
    visitors = Visitor.objects.filter(
        Q(full_name__icontains=query) |
        Q(phone__icontains=query) |
        Q(id_number__icontains=query) |
        Q(organization__icontains=query)
    ).filter(
        visits__location=request.user.assigned_location
    ).distinct()[:15]
    
    suggestions = []
    for visitor in visitors:
        # Get recent visits for this visitor
        recent_visits = visitor.visits.filter(
            location=request.user.assigned_location
        ).order_by('-check_in_time')[:3]
        
        last_visit = recent_visits.first() if recent_visits else None
        
        suggestions.append({
            'id': visitor.id,
            'text': str(visitor),
            'phone': visitor.phone,
            'full_name': visitor.full_name,
            'organization': visitor.organization or '',
            'last_visit': last_visit.check_in_time.strftime('%Y-%m-%d') if last_visit else None,
            'total_visits': visitor.visits.filter(
                location=request.user.assigned_location
            ).count(),
            'active_visits': visitor.visits.filter(
                location=request.user.assigned_location,
                status='ACTIVE'
            ).count()
        })
    
    return JsonResponse({'suggestions': suggestions})
