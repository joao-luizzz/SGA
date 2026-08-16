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
