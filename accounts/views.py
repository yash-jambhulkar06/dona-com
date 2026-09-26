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


from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.urls import reverse_lazy
from .models import User

class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').strip().lower()
        if settings.DEBUG:
            found_user = User.objects.filter(email__iexact=email, is_active=True).first()
            if found_user:
                uid = urlsafe_base64_encode(force_bytes(found_user.pk))
                token = default_token_generator.make_token(found_user)
                reset_url = self.request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                self.request.session['dev_reset_link'] = reset_url
                self.request.session['dev_reset_email'] = email
        return super().form_valid(form)


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_smtp_configured'] = bool(settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend')
        context['dev_reset_link'] = self.request.session.pop('dev_reset_link', None)
        context['dev_reset_email'] = self.request.session.pop('dev_reset_email', None)
        return context

