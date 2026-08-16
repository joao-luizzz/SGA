from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

def role_required(*allowed_roles):
    """Decorator for views to restrict access based on user role."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")

            if request.user.role not in allowed_roles and not request.user.is_superuser:
                raise PermissionDenied(_("Você não tem permissão para acessar esta página."))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
