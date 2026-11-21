from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

class RoleRequiredMixin(AccessMixin):
    """Mixin for Class-Based Views to restrict access based on allowed_roles."""
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.role not in self.allowed_roles and not request.user.is_superuser:
            raise PermissionDenied("Você não tem permissão para acessar esta página.")

        return super().dispatch(request, *args, **kwargs)
