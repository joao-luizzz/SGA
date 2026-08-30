from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TipoAvaliacao(models.TextChoices):
    P1 = 'P1', _('P1')
    P2 = 'P2', _('P2')
    TRABALHO = 'TRABALHO', _('Trabalho')
    EXAME = 'EXAME', _('Exame Final')


class Nota(models.Model):
    """Nota de uma avaliação vinculada a uma tentativa de matrícula."""

    matricula = models.ForeignKey(
        'enrollment.Matricula',
        on_delete=models.CASCADE,
        related_name='notas',
        verbose_name=_('matrícula'),
    )
    tipo = models.CharField(
        _('tipo de avaliação'),
        max_length=10,
        choices=TipoAvaliacao.choices,
    )
    valor = models.DecimalField(
        _('nota'),
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('10.00')),
        ],
    )
    registrado_por = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.PROTECT,
        related_name='notas_registradas',
        verbose_name=_('registrado por'),
    )
    criado_em = models.DateTimeField(_('criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('nota')
        verbose_name_plural = _('notas')
        ordering = ['matricula_id', 'tipo']
        constraints = [
            models.UniqueConstraint(
                fields=['matricula', 'tipo'],
                name='unique_nota_por_matricula_tipo',
            ),
            models.CheckConstraint(
                condition=models.Q(valor__gte=0) & models.Q(valor__lte=10),
                name='nota_entre_zero_e_dez',
            ),
        ]

    def __str__(self):
        return f'{self.matricula} | {self.get_tipo_display()}: {self.valor}'
