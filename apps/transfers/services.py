import json

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from academics.models import Curso
from accounts.models import CustomUser, UserRole, AcaoAuditoria
from accounts.services import registrar_auditoria

from .models import SolicitacaoTransferencia, StatusTransferencia
from .permissions import exigir_perfil


def _estado(solicitacao):
    return json.dumps({
        'aluno_id': solicitacao.aluno_id,
        'curso_id': solicitacao.curso_id,
        'tipo': solicitacao.tipo,
        'instituicao_externa': solicitacao.instituicao_externa,
        'curso_externo': solicitacao.curso_externo,
        'data_referencia': str(solicitacao.data_referencia),
        'documentos': solicitacao.documentos,
        'status': solicitacao.status,
        'solicitada_por_id': solicitacao.solicitada_por_id,
        'analisada_por_id': solicitacao.analisada_por_id,
        'analisada_em': solicitacao.analisada_em.isoformat() if solicitacao.analisada_em else None,
        'justificativa': solicitacao.justificativa,
    }, ensure_ascii=False, sort_keys=True)


@transaction.atomic
def solicitar_transferencia(*, usuario, aluno, curso, tipo, instituicao_externa,
                           curso_externo, data_referencia, documentos):
    usuario = exigir_perfil(usuario, UserRole.SECRETARIA)
    # Serializa solicitações do mesmo aluno em PostgreSQL. A constraint permanece
    # como última barreira, inclusive em inserções que não passem pelo serviço.
    aluno = CustomUser.objects.select_for_update().get(pk=aluno.pk)
    curso = Curso.objects.get(pk=curso.pk)
    if aluno.role != UserRole.ALUNO or not aluno.is_active:
        raise ValidationError({'aluno': 'Selecione um aluno ativo.'})
    if not curso.ativo:
        raise ValidationError({'curso': 'Selecione um curso ativo.'})
    solicitacao = SolicitacaoTransferencia(
        aluno=aluno, curso=curso, tipo=tipo, instituicao_externa=instituicao_externa,
        curso_externo=curso_externo, data_referencia=data_referencia,
        documentos=documentos, solicitada_por=usuario,
    )
    solicitacao.preparar_textos()
    solicitacao.full_clean()
    try:
        with transaction.atomic():
            solicitacao.save()
    except IntegrityError as exc:
        raise ValidationError('Não foi possível registrar: confira os dados e se já existe uma solicitação pendente equivalente.') from exc
    registrar_auditoria(
        usuario=usuario, tabela_afetada='SolicitacaoTransferencia',
        registro_id=solicitacao.pk, acao=AcaoAuditoria.CRIAR,
        valor_novo=_estado(solicitacao),
    )
    return solicitacao


@transaction.atomic
def analisar_transferencia(*, usuario, solicitacao_id, decisao, justificativa):
    from django.utils import timezone

    usuario = exigir_perfil(usuario, UserRole.COORDENACAO)
    if decisao not in (StatusTransferencia.APROVADA, StatusTransferencia.RECUSADA):
        raise ValidationError('Selecione aprovação ou recusa.')
    justificativa = (justificativa or '').strip()
    if not justificativa or len(justificativa) > 3000:
        raise ValidationError({'justificativa': 'Informe uma justificativa entre 1 e 3000 caracteres.'})

    solicitacao = SolicitacaoTransferencia.objects.select_for_update().get(pk=solicitacao_id)
    if solicitacao.status != StatusTransferencia.PENDENTE:
        raise ValidationError('Esta solicitação já foi analisada e não pode receber outra decisão.')
    anterior = _estado(solicitacao)
    momento = timezone.now()
    # Compare-and-set é uma barreira adicional à decisão duplicada. SQLite não
    # oferece o mesmo lock de linha; testes reais de concorrência usam PostgreSQL.
    alteradas = SolicitacaoTransferencia.objects.filter(
        pk=solicitacao.pk, status=StatusTransferencia.PENDENTE,
    ).update(status=decisao, justificativa=justificativa,
             analisada_por=usuario, analisada_em=momento)
    if alteradas != 1:
        raise ValidationError('Esta solicitação já foi analisada por outro usuário.')
    solicitacao.refresh_from_db()
    registrar_auditoria(
        usuario=usuario, tabela_afetada='SolicitacaoTransferencia',
        registro_id=solicitacao.pk, acao=AcaoAuditoria.EDITAR,
        valor_antigo=anterior, valor_novo=_estado(solicitacao),
    )
    # Aprovação administrativa: não altera Matricula, Nota, Falta ou CustomUser.
    return solicitacao
