from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .models import Profile
from tickets.models import Ticket
from .forms import EditProfileForm

def home(request):
    if request.user.is_authenticated:
        # Superuser or staff go to dashboard
        if request.user.is_superuser or request.user.is_staff:
            return redirect('dashboard:home')  # Adjust this to your actual dashboard URL name
        # Regular user (customer) goes to ticket page
        return redirect('tickets:my_tickets')
    
    # Not logged in → go to login page
    return redirect('users:login')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile.objects.create(user=user, role='user')
            messages.success(request, 'Account created successfully!')
            login(request, user)
            return redirect('tickets:my_tickets')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Absolute priority — superuser or is_staff
                if user.is_superuser or user.is_staff:
                    return redirect('dashboard:home')

                # Secondary — your profile roles
                if hasattr(user, 'profile') and user.profile.is_staff_member():
                    return redirect('dashboard:home')

                # Everyone else
                return redirect('tickets:my_tickets')

    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Logged out successfully.')
    return redirect('users:login')

@login_required
def profile(request):
    user = request.user
    total_tickets = Ticket.objects.filter(created_by=user).count()
    resolved_tickets = Ticket.objects.filter(created_by=user, status='resolved').count()
    open_tickets = Ticket.objects.filter(created_by=user, status='open').count()

    context = {
        'user': user,
        'total_tickets': total_tickets,
        'resolved_tickets': resolved_tickets,
        'open_tickets': open_tickets,
    }
    return render(request, 'users/profile.html', context)

def password_reset_request(request):
    messages.info(request, 'Password reset functionality will send email.')
    return redirect('users:login')

@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data.get('first_name')
            request.user.last_name = form.cleaned_data.get('last_name')
            request.user.email = form.cleaned_data.get('email')
            request.user.save()
            return redirect('users:profile')
    else:
        form = EditProfileForm(instance=profile)
    return render(request, 'users/edit_profile.html', {'form': form})
