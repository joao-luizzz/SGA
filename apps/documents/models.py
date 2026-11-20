from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TipoDocumento(models.TextChoices):
    DECLARACAO = 'DECLARACAO', _('Declaração de matrícula')
    HISTORICO = 'HISTORICO', _('Histórico escolar')


class DocumentoEmitidoQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValueError("Documento emitido é imutável e não pode ser alterado.")

    def delete(self):
        raise ValueError("Documento emitido é imutável e não pode ser excluído.")


class DocumentoEmitido(models.Model):
    """Documento oficial com conteúdo congelado no momento da emissão (RN21)."""

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'ALUNO'},
        related_name='documentos_emitidos',
        verbose_name=_('aluno'),
    )
    tipo = models.CharField(_('tipo'), max_length=10, choices=TipoDocumento.choices)
    codigo_verificacao = models.CharField(
        _('código de verificação'), max_length=16, unique=True, editable=False,
    )
    conteudo = models.JSONField(_('conteúdo emitido'), editable=False)
    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_('emitido por'),
    )
    emitido_em = models.DateTimeField(_('emitido em'), auto_now_add=True)

    objects = DocumentoEmitidoQuerySet.as_manager()

    class Meta:
        verbose_name = _('documento emitido')
        verbose_name_plural = _('documentos emitidos')
        ordering = ['-emitido_em', '-pk']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.aluno.full_name} ({self.codigo_verificacao})"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Documento emitido é imutável e não pode ser alterado.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Documento emitido é imutável e não pode ser excluído.")

    @property
    def codigo_formatado(self):
        codigo = self.codigo_verificacao
        return '-'.join(codigo[i:i + 4] for i in range(0, len(codigo), 4))
