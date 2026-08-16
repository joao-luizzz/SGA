from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier for authentication."""

    def create_user(self, email, full_name, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError(_("O endereço de e-mail é obrigatório."))
        if not full_name:
            raise ValueError(_("O nome completo é obrigatório."))

        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_active", True)
        
        user = self.model(email=email, full_name=full_name, role=role, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser precisa ter is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser precisa ter is_superuser=True."))

        # Default role for superuser if not provided
        from .models import UserRole
        role = extra_fields.pop("role", UserRole.COORDENACAO)

        return self.create_user(email, full_name, password, role=role, **extra_fields)
