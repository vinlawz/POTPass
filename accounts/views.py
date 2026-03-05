from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import CustomUserCreationForm, UserProfileUpdateForm
from .models import CustomUser
from core.models import Location
from visitor.models import Visit

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
                return redirect('accounts:dashboard')
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account: {str(e)}')
        else:
            # Form validation errors will be displayed automatically
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Enhanced validation
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on user role
            if user.role == 'admin':
                return redirect('accounts:admin_dashboard')
            elif user.role == 'receptionist':
                return redirect('accounts:reception_dashboard')
            else:
                return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('accounts:login')

@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
        'role': user.get_role_display() if hasattr(user, 'get_role_display') else 'User',
        'location': user.assigned_location if hasattr(user, 'assigned_location') and user.assigned_location else None
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def admin_dashboard_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('accounts:dashboard')
    
    # Get statistics for admin dashboard
    total_users = CustomUser.objects.count()
    total_locations = Location.objects.count()
    receptionists = CustomUser.objects.filter(role='receptionist')
    admins = CustomUser.objects.filter(role='admin')
    other_users = total_users - receptionists.count() - admins.count()
    
    context = {
        'total_users': total_users,
        'total_locations': total_locations,
        'receptionists': receptionists,
        'admins': admins,
        'other_users': other_users,
        'recent_users': CustomUser.objects.order_by('-date_joined')[:5]
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
def reception_dashboard_view(request):
    """Receptionist dashboard with visitor management"""
    # Get today's visits for this location
    today = timezone.now().date()
    today_visits = Visit.objects.filter(
        location=request.user.assigned_location,
        check_in_time__date=today
    ).order_by('-check_in_time')
    
    # Get statistics
    active_visits = today_visits.filter(status='ACTIVE').count()
    completed_visits = today_visits.filter(status='COMPLETED').count()
    total_visits = today_visits.count()
    
    context = {
        'location': request.user.assigned_location,
        'today_visits': today_visits,
        'active_visits': active_visits,
        'completed_visits': completed_visits,
        'total_visits': total_visits,
    }
    return render(request, 'accounts/reception_dashboard.html', context)

@login_required
def profile_view(request):
    """Display user profile details"""
    user = request.user
    context = {
        'user': user,
        'role_display': user.get_role_display(),
        'location': user.assigned_location,
        'member_since': user.date_joined,
        'last_login': user.last_login,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_update_view(request):
    """Update user profile information"""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile_update.html', {'form': form})
