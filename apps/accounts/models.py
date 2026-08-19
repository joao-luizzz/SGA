from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

class UserRole(models.TextChoices):
    ALUNO = 'ALUNO', _('Aluno')
    PROFESSOR = 'PROFESSOR', _('Professor')
    SECRETARIA = 'SECRETARIA', _('Secretaria')
    COORDENACAO = 'COORDENACAO', _('Coordenação')

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('endereço de e-mail'), unique=True, db_index=True)
    full_name = models.CharField(_('nome completo'), max_length=255)
    role = models.CharField(_('perfil'), max_length=20, choices=UserRole.choices)
    is_active = models.BooleanField(_('ativo'), default=True)
    must_change_password = models.BooleanField(
        _('deve trocar senha'),
        default=False,
        help_text=_('Indica se o usuário é obrigado a alterar a senha no próximo acesso.')
    )
    created_at = models.DateTimeField(_('data de criação'), auto_now_add=True)

    is_staff = models.BooleanField(_('membro da equipe'), default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = _('usuário')
        verbose_name_plural = _('usuários')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.get_role_display()}"

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower()


class AcaoAuditoria(models.TextChoices):
    CRIAR = 'CRIAR', _('Criar')
    EDITAR = 'EDITAR', _('Editar')
    EXCLUIR = 'EXCLUIR', _('Excluir')


class AuditoriaLog(models.Model):
    """Registro imutável de auditoria para alterações em Nota e Falta (RN30, RN31)."""

    usuario = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.PROTECT,
        related_name='logs_auditoria',
        verbose_name=_('usuário responsável'),
        null=True,
        blank=True,
    )
    tabela_afetada = models.CharField(
        _('tabela afetada'),
        max_length=50,
        help_text=_('Nome da entidade alterada, ex.: Nota ou Falta.'),
    )
    registro_id = models.BigIntegerField(_('ID do registro'))
    acao = models.CharField(
        _('ação'),
        max_length=10,
        choices=AcaoAuditoria.choices,
    )
    valor_antigo = models.TextField(_('valor anterior'), null=True, blank=True)
    valor_novo = models.TextField(_('novo valor'), null=True, blank=True)
    realizado_em = models.DateTimeField(_('realizado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('log de auditoria')
        verbose_name_plural = _('logs de auditoria')
        ordering = ['-realizado_em']
        # Imutável: ninguém pode editar ou deletar via admin (RN31)
        default_permissions = ('add', 'view')

    def __str__(self):
        return (
            f"[{self.realizado_em:%d/%m/%Y %H:%M}] "
            f"{self.acao} em {self.tabela_afetada} #{self.registro_id}"
        )

    def save(self, *args, **kwargs):
        """Impede atualização de registros existentes (imutabilidade - RN31)."""
        if self.pk:
            raise ValueError(
                "AuditoriaLog é imutável. Registros de auditoria não podem ser editados."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Impede exclusão de registros de auditoria (RN31)."""
        raise ValueError(
            "AuditoriaLog é imutável. Registros de auditoria não podem ser excluídos."
        )
