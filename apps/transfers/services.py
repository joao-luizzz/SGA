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
