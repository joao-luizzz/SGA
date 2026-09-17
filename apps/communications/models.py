from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import UserRole


class EscopoComunicado(models.TextChoices):
    GERAL = 'GERAL', _('Geral (Todos)')
    PAPEL = 'PAPEL', _('Por Perfil')
    CURSO = 'CURSO', _('Por Curso')
    TURMA = 'TURMA', _('Por Turma')


class Comunicado(models.Model):
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comunicados_publicados',
        verbose_name=_('autor')
    )
    titulo = models.CharField(_('título'), max_length=200)
    conteudo = models.TextField(_('conteúdo'))
    escopo = models.CharField(
        _('escopo'),
        max_length=20,
        choices=EscopoComunicado.choices,
        default=EscopoComunicado.GERAL
    )
    papel_destino = models.CharField(
        _('perfil de destino'),
        max_length=20,
        choices=UserRole.choices,
        blank=True,
        null=True
    )
    curso = models.ForeignKey(
        'academics.Curso',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='comunicados',
        verbose_name=_('curso')
    )
    turma = models.ForeignKey(
        'academics.Turma',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='comunicados',
        verbose_name=_('turma')
    )
    publicar_em = models.DateTimeField(_('publicar em'), default=timezone.now, blank=True)
    expirar_em = models.DateTimeField(_('expirar em'), blank=True, null=True)
    ativo = models.BooleanField(_('ativo'), default=True)
    criado_em = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('comunicado')
        verbose_name_plural = _('comunicados')
        ordering = ['-publicar_em', '-criado_em']

    def __str__(self):
        return f"[{self.get_escopo_display()}] {self.titulo}"

    def clean(self):
        super().clean()

        if self.expirar_em and self.publicar_em and self.expirar_em <= self.publicar_em:
            raise ValidationError({'expirar_em': _("A data de expiração deve ser posterior à data de publicação.")})

        if self.escopo == EscopoComunicado.GERAL:
            if self.papel_destino or self.curso or self.turma:
                raise ValidationError(_("Comunicados gerais não devem possuir perfil, curso ou turma vinculados."))

        elif self.escopo == EscopoComunicado.PAPEL:
            if not self.papel_destino:
                raise ValidationError({'papel_destino': _("Selecione o perfil de destino para este comunicado.")})
            if self.curso or self.turma:
                raise ValidationError(_("Comunicados por perfil não devem ter curso ou turma vinculados."))

        elif self.escopo == EscopoComunicado.CURSO:
            if not self.curso:
                raise ValidationError({'curso': _("Selecione o curso de destino para este comunicado.")})
            if self.papel_destino or self.turma:
                raise ValidationError(_("Comunicados por curso não devem ter perfil ou turma vinculados."))

        elif self.escopo == EscopoComunicado.TURMA:
            if not self.turma:
                raise ValidationError({'turma': _("Selecione a turma de destino para este comunicado.")})
            if self.papel_destino or self.curso:
                raise ValidationError(_("Comunicados por turma não devem ter perfil ou curso vinculados."))

    @property
    def is_vigente(self):
        agora = timezone.now()
        if not self.ativo:
            return False
        if self.publicar_em > agora:
            return False
        if self.expirar_em and self.expirar_em < agora:
            return False
        return True
