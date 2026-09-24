import hashlib
import json
import unicodedata

from django.core.exceptions import ValidationError
from django.db import models


class TipoTransferencia(models.TextChoices):
    ENTRADA = 'ENTRADA', 'Entrada'
    SAIDA = 'SAIDA', 'Saída'


class StatusTransferencia(models.TextChoices):
    PENDENTE = 'PENDENTE', 'Pendente'
    APROVADA = 'APROVADA', 'Aprovada'
    RECUSADA = 'RECUSADA', 'Recusada'


def normalizar_texto(valor):
    return ' '.join(unicodedata.normalize('NFKC', valor or '').split())


class SolicitacaoTransferencia(models.Model):
    aluno = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.PROTECT,
        related_name='transferencias', limit_choices_to={'role': 'ALUNO'},
        verbose_name='aluno',
    )
    curso = models.ForeignKey(
        'academics.Curso', on_delete=models.PROTECT,
        related_name='transferencias', verbose_name='curso na instituição atual',
    )
    tipo = models.CharField('tipo', max_length=7, choices=TipoTransferencia.choices)
    instituicao_externa = models.CharField('instituição externa', max_length=200)
    curso_externo = models.CharField('curso na instituição externa', max_length=200)
    data_referencia = models.DateField('data de referência da transferência')
    documentos = models.TextField(
        'registro dos documentos', max_length=3000,
        help_text='Liste os documentos apresentados ou justifique sua dispensa. Não informe senhas ou dados desnecessários.',
    )
    status = models.CharField(
        'situação', max_length=8, choices=StatusTransferencia.choices,
        default=StatusTransferencia.PENDENTE, editable=False,
    )
    solicitada_em = models.DateTimeField('registrada em', auto_now_add=True)
    solicitada_por = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.PROTECT,
        related_name='transferencias_registradas', editable=False,
    )
    analisada_em = models.DateTimeField('analisada em', null=True, blank=True, editable=False)
    analisada_por = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.PROTECT,
        related_name='transferencias_analisadas', null=True, blank=True, editable=False,
    )
    justificativa = models.TextField('justificativa', max_length=3000, blank=True, editable=False)
    chave_externa = models.CharField(max_length=64, editable=False, blank=True)

    class Meta:
        ordering = ['-solicitada_em', '-pk']
        verbose_name = 'solicitação de transferência'
        verbose_name_plural = 'solicitações de transferência'
        default_permissions = ('view',)
        constraints = [
            models.CheckConstraint(condition=models.Q(tipo__in=['ENTRADA', 'SAIDA']), name='transfers_tipo_valido'),
            models.CheckConstraint(
                condition=(
                    models.Q(status='PENDENTE', analisada_em__isnull=True, analisada_por__isnull=True, justificativa='')
                    | (models.Q(status__in=['APROVADA', 'RECUSADA'], analisada_em__isnull=False, analisada_por__isnull=False)
                       & ~models.Q(justificativa=''))
                ), name='transfers_decisao_consistente',
            ),
            models.CheckConstraint(
                condition=(~models.Q(instituicao_externa='') & ~models.Q(curso_externo='')
                           & ~models.Q(documentos='') & ~models.Q(chave_externa='')),
                name='transfers_dados_obrigatorios',
            ),
            models.UniqueConstraint(
                fields=['aluno', 'tipo', 'curso', 'chave_externa'],
                condition=models.Q(status='PENDENTE'), name='transfers_pendente_equivalente',
                violation_error_message='Já existe uma solicitação pendente equivalente para este aluno.',
            ),
        ]

    def preparar_textos(self):
        self.instituicao_externa = normalizar_texto(self.instituicao_externa)
        self.curso_externo = normalizar_texto(self.curso_externo)
        self.documentos = (self.documentos or '').strip()
        self.justificativa = (self.justificativa or '').strip()
        dados = [self.instituicao_externa.casefold(), self.curso_externo.casefold()]
        self.chave_externa = hashlib.sha256(json.dumps(dados, ensure_ascii=False).encode()).hexdigest()

    def clean(self):
        super().clean()
        self.preparar_textos()
        erros = {}
        for campo in ['instituicao_externa', 'curso_externo', 'documentos']:
            if not getattr(self, campo):
                erros[campo] = 'Este campo é obrigatório.'
        for campo in ['documentos', 'justificativa']:
            if len(getattr(self, campo)) > 3000:
                erros[campo] = 'Use no máximo 3000 caracteres.'
        if self.aluno_id and self.aluno.role != 'ALUNO':
            erros['aluno'] = 'Selecione um usuário com perfil de Aluno.'
        if self.status != StatusTransferencia.PENDENTE and not self.justificativa:
            erros['justificativa'] = 'Informe a justificativa da decisão.'
        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        # Mantém a chave consistente também em inserções fora do formulário.
        self.preparar_textos()
        super().save(*args, **kwargs)

    @property
    def origem(self):
        if self.tipo == TipoTransferencia.ENTRADA:
            return f'{self.instituicao_externa} — {self.curso_externo}'
        return f'Instituição atual (SGA) — {self.curso.nome}'

    @property
    def destino(self):
        if self.tipo == TipoTransferencia.SAIDA:
            return f'{self.instituicao_externa} — {self.curso_externo}'
        return f'Instituição atual (SGA) — {self.curso.nome}'

    def __str__(self):
        return f'Transferência #{self.pk} — {self.get_tipo_display()} — {self.get_status_display()}'
