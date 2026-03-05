from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Location
from .forms import LocationForm

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def location_list_view(request):
    """Display all locations with pagination and search"""
    locations = Location.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        locations = locations.filter(name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(locations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_locations': locations.count(),
    }
    return render(request, 'core/location_list.html', context)

@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def location_create_view(request):
    """Create a new location"""
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location "{location.name}" has been created successfully!')
            return redirect('core:location_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LocationForm()
    
    return render(request, 'core/location_form.html', {
        'form': form,
        'title': 'Create Location',
        'action': 'Create'
    })

@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def location_update_view(request, pk):
    """Update an existing location"""
    location = get_object_or_404(Location, pk=pk)
    
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location "{location.name}" has been updated successfully!')
            return redirect('core:location_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LocationForm(instance=location)
    
    return render(request, 'core/location_form.html', {
        'form': form,
        'location': location,
        'title': 'Update Location',
        'action': 'Update'
    })

@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def location_delete_view(request, pk):
    """Delete a location"""
    location = get_object_or_404(Location, pk=pk)
    
    if request.method == 'POST':
        # Check if location has assigned users
        if location.assigned_users.exists():
            messages.error(request, f'Cannot delete "{location.name}" because it has assigned users. Please reassign them first.')
            return redirect('core:location_list')
        
        location_name = location.name
        location.delete()
        messages.success(request, f'Location "{location_name}" has been deleted successfully!')
        return redirect('core:location_list')
    
    return render(request, 'core/location_confirm_delete.html', {
        'location': location
    })

@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def location_detail_view(request, pk):
    """Display location details and assigned users"""
    location = get_object_or_404(Location, pk=pk)
    assigned_users = location.assigned_users.all()
    
    context = {
        'location': location,
        'assigned_users': assigned_users,
        'total_assigned': assigned_users.count(),
    }
    return render(request, 'core/location_detail.html', context)
