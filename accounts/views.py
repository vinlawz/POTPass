from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .models import CustomUser
from core.models import Location

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on user role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'receptionist':
                return redirect('reception_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

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
        return redirect('dashboard')
    
    # Get statistics for admin dashboard
    total_users = CustomUser.objects.count()
    total_locations = Location.objects.count()
    receptionists = CustomUser.objects.filter(role='receptionist')
    
    context = {
        'total_users': total_users,
        'total_locations': total_locations,
        'receptionists': receptionists,
        'recent_users': CustomUser.objects.order_by('-date_joined')[:5]
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
def reception_dashboard_view(request):
    if request.user.role != 'receptionist':
        messages.error(request, 'You do not have permission to access the reception dashboard.')
        return redirect('dashboard')
    
    context = {
        'user': request.user,
        'location': request.user.assigned_location
    }
    return render(request, 'accounts/reception_dashboard.html', context)
