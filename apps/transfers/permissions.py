from django.core.exceptions import PermissionDenied

from accounts.models import CustomUser, UserRole


PAPEIS_CONSULTA = (UserRole.ALUNO, UserRole.SECRETARIA, UserRole.COORDENACAO)


def exigir_perfil(usuario, *papeis):
    """Confere também a conta persistida, sem confiar em objetos antigos do chamador."""
    if not getattr(usuario, 'is_authenticated', False) or not usuario.pk:
        raise PermissionDenied('Autentique-se para acessar transferências.')
    atual = CustomUser.objects.filter(pk=usuario.pk, is_active=True).first()
    if atual is None or (not atual.is_superuser and atual.role not in papeis):
        raise PermissionDenied('Seu perfil não pode executar esta operação de transferência.')
    return atual
