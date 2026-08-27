from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusMatricula(models.TextChoices):
    ATIVA = 'ATIVA', _('Ativa')
    TRANCADA = 'TRANCADA', _('Trancada')
    CONCLUIDA = 'CONCLUIDA', _('Concluída')
    CANCELADA = 'CANCELADA', _('Cancelada')


class Matricula(models.Model):
    """Vínculo de matrícula do Aluno na Turma (RN10, RN12)."""

    aluno = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'ALUNO'},
        related_name='matriculas',
        verbose_name=_('aluno'),
    )
    turma = models.ForeignKey(
        'academics.Turma',
        on_delete=models.CASCADE,
        related_name='matriculas',
        verbose_name=_('turma'),
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=StatusMatricula.choices,
        default=StatusMatricula.ATIVA,
    )
    matriculado_em = models.DateTimeField(_('matriculado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('matrícula')
        verbose_name_plural = _('matrículas')
        ordering = ['-matriculado_em']
        constraints = [
            models.UniqueConstraint(
                fields=['aluno', 'turma'],
                name='unique_aluno_turma',
            )
        ]

    def __str__(self):
        return f"{self.aluno.full_name} → {self.turma} [{self.get_status_display()}]"

    @property
    def esta_ativa(self):
        return self.status == StatusMatricula.ATIVA
