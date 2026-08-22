from typing import Optional
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

def create_user_by_admin(
    email: str,
    full_name: str,
    role: str,
    password: str = None,
    must_change_password: bool = True
) -> CustomUser:
    """Cria uma nova conta de usuário (apenas invocação administrativa)."""
    user = CustomUser.objects.create_user(
        email=email,
        full_name=full_name,
        role=role,
        password=password,
        must_change_password=must_change_password
    )
    return user

def authenticate_and_login_user(request, email: str, password: str) -> Optional[CustomUser]:
    """Autentica e loga um usuário se as credenciais e o status da conta forem válidos."""
    user = authenticate(request, username=email.strip().lower(), password=password)
    if user is not None:
        if not user.is_active:
            raise ValidationError(_("Esta conta está inativa. Entre em contato com a Secretaria."))
        login(request, user)
        return user
    return None

def change_user_password(user: CustomUser, new_password: str) -> CustomUser:
    """Atualiza a senha do usuário e limpa a flag must_change_password usando o hash padrão do Django."""
    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=['password', 'must_change_password'])
    return user

def toggle_user_active_status(user: CustomUser) -> CustomUser:
    """Alterna o status de ativação do usuário."""
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return user
