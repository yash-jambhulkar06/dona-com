from functools import wraps
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    """
    Decorator to ensure user is logged in and has staff (moderator) privileges.
    Returns HTTP 403 error page if user is authenticated but not authorized.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_staff:
            return render(request, 'errors/403.html', {
                'message': 'Administrator privileges are required to access this moderation resource.'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
