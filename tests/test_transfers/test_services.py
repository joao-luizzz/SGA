import json
from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from accounts.models import AuditoriaLog, CustomUser
from transfers.models import SolicitacaoTransferencia
from transfers.services import analisar_transferencia, solicitar_transferencia

pytestmark = pytest.mark.django_db


def decidir(solicitacao, usuario, decisao='APROVADA', justificativa='Documentação conferida.'):
    return analisar_transferencia(usuario=usuario, solicitacao_id=solicitacao.pk,
                                 decisao=decisao, justificativa=justificativa)


@pytest.mark.parametrize('tipo', ['ENTRADA', 'SAIDA'])
def test_solicitacao_pendente_origem_destino_e_auditoria(dados_transferencia, tipo):
    registro = solicitar_transferencia(**{**dados_transferencia, 'tipo': tipo})
    assert registro.status == 'PENDENTE'
    assert registro.analisada_em is None and registro.analisada_por is None
    assert registro.justificativa == ''
    externo = registro.origem if tipo == 'ENTRADA' else registro.destino
    interno = registro.destino if tipo == 'ENTRADA' else registro.origem
    assert 'Universidade Externa' in externo and 'Computação' in externo
    assert registro.curso.nome in interno
    log = AuditoriaLog.objects.get(tabela_afetada='SolicitacaoTransferencia')
    assert log.acao == 'CRIAR' and log.usuario == dados_transferencia['usuario']
    assert json.loads(log.valor_novo)['status'] == 'PENDENTE'


@pytest.mark.parametrize('campo,valor', [
    ('instituicao_externa', '  '), ('curso_externo', '\n'), ('documentos', ' '),
    ('data_referencia', None), ('tipo', 'INVALIDA'),
    ('instituicao_externa', 'x' * 201), ('documentos', 'x' * 3001),
])
def test_rejeita_dados_invalidos_sem_gravar(dados_transferencia, campo, valor):
    with pytest.raises(ValidationError):
        solicitar_transferencia(**{**dados_transferencia, campo: valor})
    assert not SolicitacaoTransferencia.objects.exists()
    assert not AuditoriaLog.objects.exists()


@pytest.mark.parametrize('alvo', ['aluno', 'curso', 'perfil'])
def test_revalida_cadastros_no_banco(dados_transferencia, alvo):
    aluno, curso = dados_transferencia['aluno'], dados_transferencia['curso']
    if alvo == 'curso':
        type(curso).objects.filter(pk=curso.pk).update(ativo=False)
    else:
        CustomUser.objects.filter(pk=aluno.pk).update(**(
            {'is_active': False} if alvo == 'aluno' else {'role': 'PROFESSOR'}))
    with pytest.raises(ValidationError):
        solicitar_transferencia(**dados_transferencia)


def test_duplicidade_normaliza_caixa_espacos_unicode_e_ignora_data(solicitacao, dados_transferencia):
    with pytest.raises(ValidationError):
        solicitar_transferencia(**{**dados_transferencia,
            'instituicao_externa': '  UNIVERSIDADE   EXTERNA ',
            'curso_externo': 'COMPUTAC\u0327A\u0303O', 'data_referencia': date(2027, 1, 1)})
    assert SolicitacaoTransferencia.objects.count() == 1
    assert AuditoriaLog.objects.count() == 1


def test_constraint_impede_duplicata_sem_servico(solicitacao):
    solicitacao.pk = None
    with pytest.raises(IntegrityError), transaction.atomic():
        solicitacao.save()


# O tipo inválido cabe em varchar(7), isolando a CheckConstraint também no PostgreSQL.
@pytest.mark.parametrize('alteracao', [{'status': 'APROVADA'}, {'status': 'INVALIDO'}, {'tipo': 'OUTRO'}])
def test_constraint_impede_estado_inconsistente(solicitacao, alteracao):
    with pytest.raises(IntegrityError), transaction.atomic():
        SolicitacaoTransferencia.objects.filter(pk=solicitacao.pk).update(**alteracao)


@pytest.mark.parametrize('decisao', ['APROVADA', 'RECUSADA'])
def test_decisao_tem_autor_data_justificativa_e_nao_se_repete(solicitacao, user_coordenacao, decisao):
    registro = decidir(solicitacao, user_coordenacao, decisao, '  Documentação conferida.  ')
    assert registro.status == decisao
    assert registro.analisada_por == user_coordenacao and registro.analisada_em
    assert registro.justificativa == 'Documentação conferida.'
    log = AuditoriaLog.objects.get(acao='EDITAR')
    assert json.loads(log.valor_antigo)['status'] == 'PENDENTE'
    assert json.loads(log.valor_novo)['status'] == decisao
    assert log.usuario == user_coordenacao
    with pytest.raises(ValidationError, match='já foi analisada'):
        decidir(registro, user_coordenacao, 'RECUSADA')
    assert AuditoriaLog.objects.count() == 2


@pytest.mark.parametrize('decisao,justificativa', [
    ('PENDENTE', 'OK'), ('INVALIDA', 'OK'), ('APROVADA', ''),
    ('RECUSADA', '  '), ('APROVADA', 'x' * 3001),
])
def test_decisao_invalida_nao_modifica(solicitacao, user_coordenacao, decisao, justificativa):
    with pytest.raises(ValidationError):
        decidir(solicitacao, user_coordenacao, decisao, justificativa)
    solicitacao.refresh_from_db()
    assert solicitacao.status == 'PENDENTE'
    assert AuditoriaLog.objects.count() == 1


def test_permite_nova_solicitacao_apos_decisao(solicitacao, dados_transferencia, user_coordenacao):
    decidir(solicitacao, user_coordenacao, 'RECUSADA')
    nova = solicitar_transferencia(**dados_transferencia)
    assert nova.pk != solicitacao.pk and nova.status == 'PENDENTE'


def test_decisao_administrativa_permite_cadastros_inativados(solicitacao, user_coordenacao):
    CustomUser.objects.filter(pk=solicitacao.aluno_id).update(is_active=False)
    type(solicitacao.curso).objects.filter(pk=solicitacao.curso_id).update(ativo=False)
    assert decidir(solicitacao, user_coordenacao).status == 'APROVADA'


@pytest.mark.parametrize('perfil', ['user_aluno', 'user_professor', 'user_coordenacao'])
def test_somente_secretaria_solicita(dados_transferencia, perfil, request):
    with pytest.raises(PermissionDenied):
        solicitar_transferencia(**{**dados_transferencia, 'usuario': request.getfixturevalue(perfil)})


@pytest.mark.parametrize('perfil', ['user_aluno', 'user_professor', 'user_secretaria'])
def test_somente_coordenacao_decide(solicitacao, perfil, request):
    with pytest.raises(PermissionDenied):
        decidir(solicitacao, request.getfixturevalue(perfil))


def test_anonimo_e_usuario_revogado_nao_solicitam(dados_transferencia):
    with pytest.raises(PermissionDenied):
        solicitar_transferencia(**{**dados_transferencia, 'usuario': AnonymousUser()})
    usuario = dados_transferencia['usuario']
    CustomUser.objects.filter(pk=usuario.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        solicitar_transferencia(**dados_transferencia)


def test_superusuario_ativo_pode_executar_fluxo(dados_transferencia, user_professor):
    user_professor.is_superuser = True
    user_professor.save(update_fields=['is_superuser'])
    registro = solicitar_transferencia(**{**dados_transferencia, 'usuario': user_professor})
    assert decidir(registro, user_professor).status == 'APROVADA'


def test_falha_auditoria_reverte_criacao(dados_transferencia):
    with patch('transfers.services.registrar_auditoria', side_effect=RuntimeError('Falha simulada')):
        with pytest.raises(RuntimeError):
            solicitar_transferencia(**dados_transferencia)
    assert not SolicitacaoTransferencia.objects.exists()


def test_falha_auditoria_reverte_decisao(solicitacao, user_coordenacao):
    with patch('transfers.services.registrar_auditoria', side_effect=RuntimeError('Falha simulada')):
        with pytest.raises(RuntimeError):
            decidir(solicitacao, user_coordenacao)
    solicitacao.refresh_from_db()
    assert solicitacao.status == 'PENDENTE' and solicitacao.analisada_em is None
    assert AuditoriaLog.objects.count() == 1


def test_vinculos_historicos_protegidos(solicitacao):
    for objeto in [solicitacao.aluno, solicitacao.curso, solicitacao.solicitada_por]:
        with pytest.raises(ProtectedError):
            objeto.delete()
