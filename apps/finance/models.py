from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class StatusCobranca(models.TextChoices):
    ABERTA = 'ABERTA', _('Aberta')
    PAGA = 'PAGA', _('Paga')
    CANCELADA = 'CANCELADA', _('Cancelada')


class Cobranca(models.Model):
    """Cobrança acadêmica básica, sem integração de pagamento (RN24, RN25)."""

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'ALUNO'},
        related_name='cobrancas',
        verbose_name=_('aluno'),
    )
    competencia = models.CharField(
        _('competência'), max_length=7,
        validators=[RegexValidator(r'^\d{4}-(0[1-9]|1[0-2])$', _('Use o formato AAAA-MM.'))],
    )
    descricao = models.CharField(_('descrição'), max_length=120)
    valor = models.DecimalField(_('valor'), max_digits=10, decimal_places=2)
    vencimento = models.DateField(_('vencimento'))
    status = models.CharField(
        _('situação'), max_length=10, choices=StatusCobranca.choices, default=StatusCobranca.ABERTA,
    )
    pago_em = models.DateTimeField(_('pago em'), null=True, blank=True, editable=False)
    justificativa = models.TextField(_('justificativa do cancelamento'), max_length=1000, blank=True, editable=False)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', verbose_name=_('registrado por'),
    )
    registrado_em = models.DateTimeField(_('registrado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('cobrança')
        verbose_name_plural = _('cobranças')
        ordering = ['-vencimento', '-pk']
        constraints = [
            models.CheckConstraint(condition=models.Q(valor__gt=0), name='cobranca_valor_positivo'),
            models.CheckConstraint(
                condition=(
                    models.Q(status='ABERTA', pago_em__isnull=True, justificativa='')
                    | models.Q(status='PAGA', pago_em__isnull=False, justificativa='')
                    | (models.Q(status='CANCELADA', pago_em__isnull=True) & ~models.Q(justificativa=''))
                ),
                name='cobranca_estado_coerente',
            ),
            models.UniqueConstraint(
                fields=['aluno', 'competencia', 'descricao'],
                condition=~models.Q(status='CANCELADA'),
                name='cobranca_unica_por_competencia',
            ),
        ]

    def __str__(self):
        return f"{self.aluno.full_name} — {self.descricao} {self.competencia} [{self.get_status_display()}]"

    @property
    def em_atraso(self):
        """Derivado, não persistido (RN24)."""
        return self.status == StatusCobranca.ABERTA and self.vencimento < timezone.localdate()
