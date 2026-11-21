from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class Falta(models.Model):
    """Registro diário de presença/ausência por aula (RN21)."""

    turma = models.ForeignKey(
        'academics.Turma',
        on_delete=models.CASCADE,
        related_name='faltas',
        verbose_name=_('turma'),
    )
    aluno = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'ALUNO'},
        related_name='faltas',
        verbose_name=_('aluno'),
    )
    data_aula = models.DateField(_('data da aula'))
    presente = models.BooleanField(
        _('presente'),
        help_text=_('Marque se o aluno esteve presente nesta aula.'),
    )
    registrado_por = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'PROFESSOR'},
        related_name='chamadas_registradas',
        verbose_name=_('registrado por'),
    )
    registrado_em = models.DateTimeField(_('registrado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('registro de frequência')
        verbose_name_plural = _('registros de frequência')
        ordering = ['-data_aula', 'aluno__full_name']
        constraints = [
            models.UniqueConstraint(
                fields=['turma', 'aluno', 'data_aula'],
                name='unique_chamada_por_aula',
            )
        ]

    def __str__(self):
        situacao = _('Presente') if self.presente else _('Ausente')
        return f"{self.aluno.full_name} | {self.turma} | {self.data_aula} → {situacao}"

    def clean(self):
        super().clean()
        # Verifica que o aluno possui matrícula ativa nesta turma
        from enrollment.models import Matricula, StatusMatricula
        if self.aluno_id and self.turma_id:
            matriculado = Matricula.objects.filter(
                aluno_id=self.aluno_id,
                turma_id=self.turma_id,
                status=StatusMatricula.ATIVA,
            ).exists()
            if not matriculado:
                raise ValidationError(
                    _("O aluno %(aluno)s não possui matrícula ativa nesta turma.") % {
                        'aluno': self.aluno.full_name if self.aluno_id else '?'
                    }
                )
