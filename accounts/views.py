from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm, LoginForm


def login_view(request):
    """User login page with email and password."""
    if request.user.is_authenticated:
        return redirect('food:home')

    redirect_to = request.POST.get('next') or request.GET.get('next') or reverse('food:home')

    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.full_name}!")
            return redirect(redirect_to)
    else:
        form = LoginForm(request=request)

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': redirect_to,
    })


def register_view(request):
    """User registration page for Full Name, Email, Password, and Confirm Password."""
    if request.user.is_authenticated:
        return redirect('food:home')

    redirect_to = request.POST.get('next') or request.GET.get('next') or reverse('food:home')

    if request.method == 'POST':
        form = RegisterForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Dona.Com, {user.full_name}! Your account has been created.")
            return redirect(redirect_to)
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'next': redirect_to,
    })


def logout_view(request):
    """Logs out the user and cleans up the session."""
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect('food:home')


@login_required
def profile_view(request):
    """User profile page showing user details, submissions count, and favorites."""
    submissions_count = request.user.submissions.count()
    favorites_count = request.user.favorites.count()
    return render(request, 'accounts/profile.html', {
        'submissions_count': submissions_count,
        'favorites_count': favorites_count,
    })
