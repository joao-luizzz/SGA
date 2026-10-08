from typing import Optional

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.db import transaction
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, AcaoAuditoria, AuditoriaLog

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

@sensitive_variables('new_password')
def change_user_password(user: CustomUser, new_password: str) -> CustomUser:
    """Atualiza a senha do usuário e limpa a flag must_change_password usando o hash padrão do Django."""
    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=['password', 'must_change_password'])
    return user

def registrar_auditoria(
    usuario: Optional[CustomUser],
    tabela_afetada: str,
    registro_id: int,
    acao: str,
    valor_antigo: Optional[str] = None,
    valor_novo: Optional[str] = None,
) -> AuditoriaLog:
    """
    Registra uma entrada imutável de auditoria para alterações em Nota ou Falta (RN30).

    Args:
        usuario: Usuário responsável pela ação (professor ou secretaria).
        tabela_afetada: Nome da entidade, ex.: 'Falta' ou 'Nota'.
        registro_id: ID do registro afetado.
        acao: Um dos valores de AcaoAuditoria ('CRIAR', 'EDITAR', 'EXCLUIR').
        valor_antigo: Representação do estado anterior (opcional).
        valor_novo: Representação do novo estado (opcional).

    Returns:
        AuditoriaLog criado e persistido.
    """
    log = AuditoriaLog(
        usuario=usuario,
        tabela_afetada=tabela_afetada,
        registro_id=registro_id,
        acao=acao,
        valor_antigo=valor_antigo,
        valor_novo=valor_novo,
    )
    log.save()
    return log


def toggle_user_active_status(user: CustomUser) -> CustomUser:
    """Alterna o status de ativação do usuário."""
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return user


def solicitar_recuperacao(form, request):
    """Mesmo resultado público para contas ausentes, inelegíveis e throttling."""
    email = form.cleaned_data['email'].strip().lower()
    for namespace, value, timeout in (
        ('email', email, settings.PASSWORD_RESET_EMAIL_COOLDOWN),
        ('ip', request.META.get('REMOTE_ADDR', ''), settings.PASSWORD_RESET_IP_COOLDOWN),
    ):
        key = salted_hmac('sga-recovery-' + namespace, value).hexdigest()
        if timeout and not cache.add('recovery:' + key, True, timeout):
            return
    form.save(
        request=request,
        domain_override=settings.PASSWORD_RESET_DOMAIN,
        use_https=settings.PASSWORD_RESET_USE_HTTPS,
        from_email=settings.DEFAULT_FROM_EMAIL,
        email_template_name='registration/password_reset_email.txt',
        subject_template_name='registration/password_reset_subject.txt',
    )


@sensitive_variables()
@transaction.atomic
def redefinir_senha(*, user_id, token, password):
    # Reavaliar o token DEPOIS do bloqueio evita dois POSTs aceitos com o mesmo token.
    user = CustomUser.objects.select_for_update().filter(pk=user_id).first()
    if (
        not user or not user.is_active or not user.has_usable_password()
        or not default_token_generator.check_token(user, token)
    ):
        raise ValidationError('Link inválido ou expirado. Solicite uma nova recuperação.')
    password_validation.validate_password(password, user)
    change_user_password(user, password)
    registrar_auditoria(
        usuario=user, tabela_afetada='CustomUser', registro_id=user.pk,
        acao=AcaoAuditoria.EDITAR, valor_novo='Senha redefinida por recuperação.',
    )
    return user
