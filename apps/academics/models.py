from django.db import models
from django.utils.translation import gettext_lazy as _

class Curso(models.Model):
    nome = models.CharField(_('nome'), max_length=150)
    codigo = models.CharField(_('código'), max_length=20, unique=True)
    descricao = models.TextField(_('descrição'), blank=True, null=True)
    ativo = models.BooleanField(_('ativo'), default=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('curso')
        verbose_name_plural = _('cursos')
        ordering = ['nome']

    def __str__(self):
        status = "" if self.ativo else f" ({_('Inativo')})"
        return f"{self.nome} - {self.codigo}{status}"


class Disciplina(models.Model):
    nome = models.CharField(_('nome'), max_length=100)
    codigo = models.CharField(_('código'), max_length=20, unique=True)
    carga_horaria = models.PositiveIntegerField(_('carga horária'))
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='disciplinas',
        verbose_name=_('curso')
    )
    ativo = models.BooleanField(_('ativo'), default=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('disciplina')
        verbose_name_plural = _('disciplinas')
        ordering = ['nome']

    def __str__(self):
        status = "" if self.ativo else f" ({_('Inativa')})"
        return f"{self.nome} - {self.codigo} ({self.carga_horaria}h){status}"
