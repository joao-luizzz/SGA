from typing import Optional
from django.urls import reverse
from .models import CustomUser, UserRole

def get_user_by_email(email: str) -> Optional[CustomUser]:
    """Retrieve user by normalized email address."""
    if not email:
        return None
    return CustomUser.objects.filter(email__iexact=email.strip()).first()

def get_dashboard_url_by_role(role: str) -> str:
    """Return the dashboard URL corresponding to the user's role."""
    role_dashboard_map = {
        UserRole.ALUNO: reverse('accounts:dashboard_aluno'),
        UserRole.PROFESSOR: reverse('accounts:dashboard_professor'),
        UserRole.SECRETARIA: reverse('accounts:dashboard_secretaria'),
        UserRole.COORDENACAO: reverse('accounts:dashboard_coordenacao'),
    }
    return role_dashboard_map.get(role, reverse('accounts:login'))

def list_manageable_users():
    """Retorna a lista de alunos e professores ordenados por nome."""
    return CustomUser.objects.filter(role__in=[UserRole.ALUNO, UserRole.PROFESSOR]).order_by('full_name')
