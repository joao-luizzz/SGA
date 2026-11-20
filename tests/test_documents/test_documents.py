from datetime import date
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from academics.models import Curso, Disciplina, StatusAproveitamento, Turma
from academics.services import analisar_aproveitamento, registrar_aproveitamento
from accounts.models import AcaoAuditoria, AuditoriaLog, CustomUser, UserRole
from assessments.models import Nota, TipoAvaliacao
from attendance.models import Falta
from documents.models import DocumentoEmitido, TipoDocumento
from documents.services import (
    LIMITE_VERIFICACOES, emitir_documento, mascarar_nome, normalizar_codigo, verificar_documento,
)
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture(autouse=True)
def limpar_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def curso(db):
    return Curso.objects.create(nome='Sistemas', codigo='SI')


def _turma(curso, professor, nome, codigo, periodo, horarios):
    disciplina = Disciplina.objects.create(nome=nome, codigo=codigo, carga_horaria=60, curso=curso)
    return Turma.objects.create(disciplina=disciplina, periodo_letivo=periodo, horarios=horarios,
                                sala='A1', vagas_maximas=10, professor=professor)


def _notas(matricula, professor, *valores):
    for tipo, valor in zip((TipoAvaliacao.P1, TipoAvaliacao.P2, TipoAvaliacao.TRABALHO), valores):
        Nota.objects.create(matricula=matricula, tipo=tipo, valor=Decimal(valor), registrado_por=professor)


@pytest.fixture
def historico(curso, user_aluno, user_professor):
    """Aluno com uma aprovação, uma reprovação por falta, uma em andamento e uma cancelada."""
    aprovada = Matricula.objects.create(
        aluno=user_aluno, turma=_turma(curso, user_professor, 'Algoritmos', 'ALG', '2025/2', 'SEG 08:00-10:00'))
    _notas(aprovada, user_professor, 8, 7, 9)
    faltosa = Matricula.objects.create(
        aluno=user_aluno, turma=_turma(curso, user_professor, 'Banco de Dados', 'BD', '2025/2', 'TER 08:00-10:00'))
    _notas(faltosa, user_professor, 9, 9, 9)
    for dia, presente in enumerate([True, False, False, False], start=1):
        Falta.objects.create(turma=faltosa.turma, aluno=user_aluno, data_aula=date(2025, 9, dia),
                             presente=presente, registrado_por=user_professor)
    Matricula.objects.create(
        aluno=user_aluno, turma=_turma(curso, user_professor, 'Redes', 'RED', '2026/1', 'QUA 08:00-10:00'))
    cancelada = Matricula.objects.create(
        aluno=user_aluno, turma=_turma(curso, user_professor, 'Cálculo', 'CAL', '2025/1', 'QUI 08:00-10:00'),
        status=StatusMatricula.CANCELADA)
    _notas(cancelada, user_professor, 10, 10, 10)
    return aprovada


@pytest.fixture
def outro_aluno(db):
    return CustomUser.objects.create_user(email='outro@sga.edu.br', full_name='Outro Aluno',
                                          role=UserRole.ALUNO, password='x', must_change_password=False)


# --- Emissão (RN21, RN22) ----------------------------------------------------

@pytest.mark.django_db
def test_declaracao_lista_somente_matriculas_ativas(historico, user_aluno):
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.DECLARACAO)

    disciplinas = [item['disciplina'] for item in documento.conteudo['matriculas']]
    assert disciplinas == ['Algoritmos', 'Banco de Dados', 'Redes']
    assert documento.conteudo['aluno']['nome'] == 'Aluno Teste'
    assert len(documento.codigo_verificacao) == 16


@pytest.mark.django_db
def test_declaracao_exige_matricula_ativa(user_aluno, user_secretaria):
    with pytest.raises(ValidationError, match='matrícula ativa'):
        emitir_documento(usuario=user_secretaria, aluno=user_aluno, tipo=TipoDocumento.DECLARACAO)
    assert not DocumentoEmitido.objects.exists()


@pytest.mark.django_db
def test_historico_lista_resultados_finais_e_carga_aprovada(historico, user_aluno):
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.HISTORICO)

    linhas = {item['disciplina']: item for item in documento.conteudo['disciplinas']}
    assert set(linhas) == {'Algoritmos', 'Banco de Dados'}
    assert linhas['Algoritmos']['situacao'] == 'Aprovado Direto'
    assert linhas['Algoritmos']['media_parcial'] == '8.00'
    assert linhas['Banco de Dados']['situacao'] == 'Reprovado por Falta'
    assert documento.conteudo['carga_horaria_integralizada'] == 60


@pytest.mark.django_db
def test_historico_inclui_aproveitamento_deferido(
    curso, user_aluno, user_secretaria, user_coordenacao,
):
    disciplina = Disciplina.objects.create(nome='Lógica', codigo='LOG', carga_horaria=40, curso=curso)
    registro = registrar_aproveitamento(usuario=user_secretaria, aluno=user_aluno, disciplina=disciplina,
                                        instituicao_origem='UFX', disciplina_origem='Lógica I',
                                        carga_horaria_origem=40)
    analisar_aproveitamento(usuario=user_coordenacao, aproveitamento_id=registro.pk,
                            decisao=StatusAproveitamento.DEFERIDO, justificativa='Equivalente.')

    documento = emitir_documento(usuario=user_secretaria, aluno=user_aluno, tipo=TipoDocumento.HISTORICO)

    assert documento.conteudo['aproveitamentos'][0]['disciplina'] == 'Lógica'
    assert documento.conteudo['carga_horaria_integralizada'] == 40


@pytest.mark.django_db
def test_conteudo_emitido_nao_muda_com_alteracao_posterior(historico, user_aluno, user_professor):
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.HISTORICO)
    Nota.objects.filter(matricula=historico, tipo=TipoAvaliacao.P1).update(valor=Decimal('1'))

    documento.refresh_from_db()
    assert documento.conteudo['disciplinas'][0]['media_parcial'] == '8.00'


@pytest.mark.django_db
def test_documento_e_imutavel(historico, user_aluno):
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.DECLARACAO)

    with pytest.raises(ValueError):
        documento.save()
    with pytest.raises(ValueError):
        documento.delete()
    with pytest.raises(ValueError):
        DocumentoEmitido.objects.filter(pk=documento.pk).update(tipo=TipoDocumento.HISTORICO)
    with pytest.raises(ValueError):
        DocumentoEmitido.objects.all().delete()


@pytest.mark.django_db
def test_emissao_registra_auditoria(historico, user_secretaria, user_aluno):
    documento = emitir_documento(usuario=user_secretaria, aluno=user_aluno, tipo=TipoDocumento.DECLARACAO)

    log = AuditoriaLog.objects.get(tabela_afetada='DocumentoEmitido', registro_id=documento.pk)
    assert log.acao == AcaoAuditoria.CRIAR
    assert log.usuario == user_secretaria
    assert documento.codigo_verificacao in log.valor_novo


@pytest.mark.django_db
def test_aluno_nao_emite_documento_de_outro(user_aluno, outro_aluno):
    with pytest.raises(PermissionDenied):
        emitir_documento(usuario=user_aluno, aluno=outro_aluno, tipo=TipoDocumento.HISTORICO)


@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_professor', 'user_coordenacao'])
def test_outros_perfis_nao_emitem(request, fixture, user_aluno):
    with pytest.raises(PermissionDenied):
        emitir_documento(usuario=request.getfixturevalue(fixture), aluno=user_aluno,
                         tipo=TipoDocumento.HISTORICO)


@pytest.mark.django_db
def test_nao_emite_para_quem_nao_e_aluno(user_secretaria, user_professor):
    with pytest.raises(ValidationError, match='alunos'):
        emitir_documento(usuario=user_secretaria, aluno=user_professor, tipo=TipoDocumento.HISTORICO)


# --- Verificação pública (RN23) ---------------------------------------------

def test_mascara_nome_e_normaliza_codigo():
    assert mascarar_nome('Maria da Silva Souza') == 'Maria D. S. S.'
    assert mascarar_nome('Ana') == 'Ana'
    assert normalizar_codigo(' ab12-cd34 ef56-7890 ') == 'AB12CD34EF567890'


@pytest.mark.django_db
def test_verificacao_confirma_documento_sem_dados_academicos(historico, user_aluno):
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.HISTORICO)

    resultado = verificar_documento(codigo=documento.codigo_formatado.lower(), ip='10.0.0.1')

    assert resultado['aluno'] == 'Aluno T.'
    assert resultado['tipo'] == 'Histórico escolar'
    assert set(resultado) == {'tipo', 'emitido_em', 'aluno', 'codigo'}


@pytest.mark.django_db
@pytest.mark.parametrize('codigo', ['', 'ABC', '0000000000000000', 'ZZZZZZZZZZZZZZZZ'])
def test_verificacao_codigo_invalido_ou_inexistente(codigo):
    assert verificar_documento(codigo=codigo, ip='10.0.0.2') is None


@pytest.mark.django_db
def test_verificacao_limita_tentativas_por_ip(historico, user_aluno):
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.DECLARACAO)
    for _ in range(LIMITE_VERIFICACOES):
        verificar_documento(codigo='0000000000000000', ip='10.0.0.3')

    assert verificar_documento(codigo=documento.codigo_verificacao, ip='10.0.0.3') is None
    assert verificar_documento(codigo=documento.codigo_verificacao, ip='10.0.0.4') is not None


# --- Views e RBAC ------------------------------------------------------------

@pytest.mark.django_db
def test_aluno_emite_e_abre_o_proprio_documento(client, historico, user_aluno):
    client.force_login(user_aluno)

    resposta = client.post(reverse('documents:emitir'), {'tipo': 'HISTORICO'})

    documento = DocumentoEmitido.objects.get()
    assert resposta.status_code == 302
    assert resposta.url == reverse('documents:detalhe', args=[documento.pk])
    pagina = client.get(resposta.url).content.decode()
    assert 'Algoritmos' in pagina
    assert documento.codigo_formatado in pagina


@pytest.mark.django_db
def test_aluno_ignora_campo_aluno_e_emite_para_si(client, historico, user_aluno, outro_aluno):
    client.force_login(user_aluno)

    client.post(reverse('documents:emitir'), {'tipo': 'HISTORICO', 'aluno': outro_aluno.pk})

    assert DocumentoEmitido.objects.get().aluno == user_aluno


@pytest.mark.django_db
def test_aluno_nao_acessa_documento_de_outro(client, user_secretaria, outro_aluno, user_aluno):
    alheio = emitir_documento(usuario=user_secretaria, aluno=outro_aluno, tipo=TipoDocumento.HISTORICO)
    client.force_login(user_aluno)

    assert client.get(reverse('documents:detalhe', args=[alheio.pk])).status_code == 404
    assert list(client.get(reverse('documents:index')).context['page_obj']) == []


@pytest.mark.django_db
def test_secretaria_emite_para_aluno_selecionado(client, historico, user_secretaria, user_aluno):
    client.force_login(user_secretaria)

    resposta = client.post(reverse('documents:emitir'), {'tipo': 'DECLARACAO', 'aluno': user_aluno.pk})

    assert resposta.status_code == 302
    documento = DocumentoEmitido.objects.get()
    assert documento.aluno == user_aluno and documento.emitido_por == user_secretaria


@pytest.mark.django_db
def test_secretaria_sem_aluno_ou_declaracao_invalida_volta_com_mensagem(client, user_secretaria, user_aluno):
    client.force_login(user_secretaria)

    sem_aluno = client.post(reverse('documents:emitir'), {'tipo': 'DECLARACAO'}, follow=True)
    sem_matricula = client.post(reverse('documents:emitir'),
                                {'tipo': 'DECLARACAO', 'aluno': user_aluno.pk}, follow=True)

    assert 'Selecione o aluno' in sem_aluno.content.decode()
    assert 'matrícula ativa' in sem_matricula.content.decode()
    assert not DocumentoEmitido.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_professor', 'user_coordenacao'])
def test_professor_e_coordenacao_nao_acessam_documentos(client, request, fixture):
    client.force_login(request.getfixturevalue(fixture))

    assert client.get(reverse('documents:index')).status_code == 403
    assert client.post(reverse('documents:emitir'), {'tipo': 'HISTORICO'}).status_code == 403


@pytest.mark.django_db
def test_verificacao_publica_funciona_sem_login(client, historico, user_aluno):
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.HISTORICO)

    valido = client.get(reverse('documents:verificar'), {'codigo': documento.codigo_formatado})
    invalido = client.get(reverse('documents:verificar'), {'codigo': '0000-0000-0000-0000'})

    assert valido.status_code == 200
    conteudo = valido.content.decode()
    assert 'Documento autêntico' in conteudo and 'Aluno T.' in conteudo
    assert 'Algoritmos' not in conteudo and user_aluno.email not in conteudo
    assert valido['Referrer-Policy'] == 'no-referrer'
    assert 'Não foi possível confirmar' in invalido.content.decode()
