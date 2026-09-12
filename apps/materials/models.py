import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.zip', '.rar', '.tar', '.gz', '.png', '.jpg', '.jpeg',
    '.webp', '.mp4', '.csv'
}


class MaterialAcademico(models.Model):
    turma = models.ForeignKey(
        'academics.Turma',
        on_delete=models.CASCADE,
        related_name='materiais',
        verbose_name=_('turma')
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='materiais_publicados',
        verbose_name=_('autor')
    )
    titulo = models.CharField(_('título'), max_length=200)
    descricao = models.TextField(_('descrição'), blank=True)
    arquivo = models.FileField(
        _('arquivo'),
        upload_to='materiais/%Y/%m/',
        blank=True,
        null=True
    )
    link = models.URLField(_('link externo'), max_length=500, blank=True, null=True)
    criado_em = models.DateTimeField(_('criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('material acadêmico')
        verbose_name_plural = _('materiais acadêmicos')
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.titulo} - {self.turma}"

    def clean(self):
        super().clean()
        tem_arquivo = bool(self.arquivo)
        tem_link = bool(self.link and self.link.strip())

        if not tem_arquivo and not tem_link:
            raise ValidationError(_("É necessário fornecer um arquivo OU um link externo."))

        if tem_arquivo and tem_link:
            raise ValidationError(_("Forneça apenas um arquivo OU um link externo, não ambos."))

        if tem_arquivo and hasattr(self.arquivo, 'size') and self.arquivo.size:
            if self.arquivo.size > MAX_FILE_SIZE:
                raise ValidationError(_("O arquivo excede o limite máximo permitido de 20 MB."))

            ext = os.path.splitext(self.arquivo.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise ValidationError(
                    _("Tipo de arquivo '%(ext)s' não permitido. Extensões aceitas: %(exts)s.") % {
                        'ext': ext,
                        'exts': ', '.join(sorted(ALLOWED_EXTENSIONS))
                    }
                )

    @property
    def is_link(self):
        return bool(self.link)

    @property
    def filename(self):
        if self.arquivo:
            return os.path.basename(self.arquivo.name)
        return ""
