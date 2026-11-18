from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from academics.models import (
    Aproveitamento, Curso, Disciplina, PreRequisito, StatusAproveitamento, Turma,
)
from academics.services import (
    adicionar_pre_requisito, analisar_aproveitamento, registrar_aproveitamento,
    remover_pre_requisito,
)
from accounts.models import AcaoAuditoria, AuditoriaLog, CustomUser, UserRole
from assessments.models import Nota, TipoAvaliacao
from attendance.models import Falta
from enrollment.models import Matricula, StatusMatricula
from enrollment.services import matricular_aluno_administrativo


@pytest.fixture
def curso(db):
    return Curso.objects.create(nome='Sistemas', codigo='SI')


@pytest.fixture
def calculo1(curso):
    return Disciplina.objects.create(nome='Cálculo I', codigo='CAL1', carga_horaria=80, curso=curso)


@pytest.fixture
def calculo2(curso):
    return Disciplina.objects.create(nome='Cálculo II', codigo='CAL2', carga_horaria=80, curso=curso)


@pytest.fixture
def calculo3(curso):
    return Disciplina.objects.create(nome='Cálculo III', codigo='CAL3', carga_horaria=80, curso=curso)


def _turma(disciplina, professor, periodo='2026/1', horarios='SEG 08:00-10:00'):
    return Turma.objects.create(
        disciplina=disciplina, periodo_letivo=periodo, horarios=horarios,
        sala='Sala 1', vagas_maximas=10, professor=professor, ativo=True,
    )


def _notas(matricula, professor, p1, p2, trabalho, exame=None):
    valores = {TipoAvaliacao.P1: p1, TipoAvaliacao.P2: p2, TipoAvaliacao.TRABALHO: trabalho}
    if exame is not None:
        valores[TipoAvaliacao.EXAME] = exame
    for tipo, valor in valores.items():
        Nota.objects.create(
            matricula=matricula, tipo=tipo, valor=Decimal(str(valor)), registrado_por=professor,
        )


@pytest.fixture
def cenario(calculo1, calculo2, user_professor, user_aluno, user_coordenacao):
    """Cálculo II exige Cálculo I; o aluno já cursou uma turma de Cálculo I."""
    adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)
    turma_anterior = _turma(calculo1, user_professor, periodo='2025/2')
    matricula_anterior = Matricula.objects.create(aluno=user_aluno, turma=turma_anterior)
    turma_nova = _turma(calculo2, user_professor, horarios='TER 08:00-10:00')
    return {'matricula_anterior': matricula_anterior, 'turma_nova': turma_nova}


# --- Cadastro de pré-requisitos (RN18) ---------------------------------------

@pytest.mark.django_db
def test_adicionar_pre_requisito_registra_auditoria(user_coordenacao, calculo1, calculo2):
    item = adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)

    assert list(calculo2.pre_requisitos.values_list('requisito_id', flat=True)) == [calculo1.pk]
    log = AuditoriaLog.objects.get(tabela_afetada='PreRequisito', registro_id=item.pk)
    assert log.acao == AcaoAuditoria.CRIAR
    assert log.usuario == user_coordenacao


@pytest.mark.django_db
def test_recusa_autorreferencia(user_coordenacao, calculo1):
    with pytest.raises(ValidationError, match='si mesma'):
        adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo1, requisito=calculo1)


@pytest.mark.django_db
def test_constraint_impede_autorreferencia_no_banco(calculo1):
    with pytest.raises(IntegrityError), transaction.atomic():
        PreRequisito.objects.create(disciplina=calculo1, requisito=calculo1)


@pytest.mark.django_db
def test_recusa_disciplina_de_outro_curso(user_coordenacao, calculo1):
    outro = Curso.objects.create(nome='Direito', codigo='DIR')
    externa = Disciplina.objects.create(nome='Civil', codigo='CIV', carga_horaria=60, curso=outro)

    with pytest.raises(ValidationError, match='mesmo curso'):
        adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo1, requisito=externa)


@pytest.mark.django_db
def test_recusa_disciplina_inativa(user_coordenacao, calculo1, calculo2):
    calculo1.ativo = False
    calculo1.save(update_fields=['ativo'])

    with pytest.raises(ValidationError, match='ativas'):
        adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)


@pytest.mark.django_db
def test_recusa_duplicado(user_coordenacao, calculo1, calculo2):
    adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)

    with pytest.raises(ValidationError, match='já está cadastrado'):
        adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)


@pytest.mark.django_db
def test_recusa_ciclo_direto(user_coordenacao, calculo1, calculo2):
    adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)

    with pytest.raises(ValidationError, match='ciclo'):
        adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo1, requisito=calculo2)


@pytest.mark.django_db
def test_recusa_ciclo_indireto(user_coordenacao, calculo1, calculo2, calculo3):
    adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)
    adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo3, requisito=calculo2)

    with pytest.raises(ValidationError, match='ciclo'):
        adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo1, requisito=calculo3)
    assert PreRequisito.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_secretaria', 'user_professor', 'user_aluno'])
def test_somente_coordenacao_mantem_pre_requisitos(request, fixture, calculo1, calculo2):
    usuario = request.getfixturevalue(fixture)

    with pytest.raises(PermissionDenied):
        adicionar_pre_requisito(usuario=usuario, disciplina=calculo2, requisito=calculo1)


@pytest.mark.django_db
def test_remover_pre_requisito_registra_exclusao(user_coordenacao, calculo1, calculo2):
    item = adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)

    remover_pre_requisito(usuario=user_coordenacao, pre_requisito_id=item.pk)

    assert not PreRequisito.objects.exists()
    log = AuditoriaLog.objects.get(tabela_afetada='PreRequisito', acao=AcaoAuditoria.EXCLUIR)
    assert log.registro_id == item.pk


# --- Matrícula com pré-requisito (RN19) --------------------------------------

@pytest.mark.django_db
def test_matricula_bloqueada_sem_resultado_no_pre_requisito(cenario, user_secretaria, user_aluno):
    with pytest.raises(ValidationError, match='pré-requisitos da disciplina: Cálculo I'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])
    assert not Matricula.objects.filter(turma=cenario['turma_nova']).exists()


@pytest.mark.django_db
def test_matricula_liberada_com_aprovacao_direta(cenario, user_secretaria, user_aluno, user_professor):
    _notas(cenario['matricula_anterior'], user_professor, 7, 8, 9)

    matricula = matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])

    assert matricula.status == StatusMatricula.ATIVA


@pytest.mark.django_db
def test_matricula_liberada_com_aprovacao_apos_exame(cenario, user_secretaria, user_aluno, user_professor):
    _notas(cenario['matricula_anterior'], user_professor, 5, 5, 5, exame=8)

    assert matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])


@pytest.mark.django_db
@pytest.mark.parametrize('notas', [
    (5, 5, 5, None),   # elegível a exame, sem exame lançado
    (2, 3, 3, None),   # reprovado por nota
    (5, 5, 5, 4),      # reprovado após exame
])
def test_matricula_bloqueada_sem_aprovacao(cenario, user_secretaria, user_aluno, user_professor, notas):
    p1, p2, trabalho, exame = notas
    _notas(cenario['matricula_anterior'], user_professor, p1, p2, trabalho, exame=exame)

    with pytest.raises(ValidationError, match='pré-requisitos'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])


@pytest.mark.django_db
def test_matricula_bloqueada_com_reprovacao_por_falta(cenario, user_secretaria, user_aluno, user_professor):
    anterior = cenario['matricula_anterior']
    _notas(anterior, user_professor, 10, 10, 10)
    for dia, presente in enumerate([True, False, False, False], start=1):
        Falta.objects.create(
            turma=anterior.turma, aluno=user_aluno, data_aula=date(2025, 9, dia),
            presente=presente, registrado_por=user_professor,
        )

    with pytest.raises(ValidationError, match='pré-requisitos'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])


@pytest.mark.django_db
def test_matricula_cancelada_nao_cumpre_pre_requisito(cenario, user_secretaria, user_aluno, user_professor):
    anterior = cenario['matricula_anterior']
    _notas(anterior, user_professor, 9, 9, 9)
    anterior.status = StatusMatricula.CANCELADA
    anterior.save(update_fields=['status'])

    with pytest.raises(ValidationError, match='pré-requisitos'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])


@pytest.mark.django_db
def test_aproveitamento_deferido_cumpre_pre_requisito(
    cenario, user_secretaria, user_coordenacao, user_aluno, calculo1,
):
    registro = registrar_aproveitamento(
        usuario=user_secretaria, aluno=user_aluno, disciplina=calculo1,
        instituicao_origem='UFX', disciplina_origem='Cálculo A', carga_horaria_origem=80,
    )
    with pytest.raises(ValidationError, match='pré-requisitos'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])

    analisar_aproveitamento(
        usuario=user_coordenacao, aproveitamento_id=registro.pk,
        decisao=StatusAproveitamento.DEFERIDO, justificativa='Ementa equivalente.',
    )

    assert matricular_aluno_administrativo(user_secretaria, user_aluno, cenario['turma_nova'])


@pytest.mark.django_db
def test_disciplina_sem_pre_requisito_continua_livre(user_secretaria, user_aluno, user_professor, calculo1):
    turma = _turma(calculo1, user_professor)

    assert matricular_aluno_administrativo(user_secretaria, user_aluno, turma)


# --- Aproveitamento (RN20) ---------------------------------------------------

@pytest.fixture
def aproveitamento(user_secretaria, user_aluno, calculo1):
    return registrar_aproveitamento(
        usuario=user_secretaria, aluno=user_aluno, disciplina=calculo1,
        instituicao_origem='  UFX  ', disciplina_origem='Cálculo A', carga_horaria_origem=60,
    )


@pytest.mark.django_db
def test_registrar_aproveitamento_pendente_com_auditoria(aproveitamento, user_secretaria):
    assert aproveitamento.status == StatusAproveitamento.PENDENTE
    assert aproveitamento.instituicao_origem == 'UFX'
    log = AuditoriaLog.objects.get(tabela_afetada='Aproveitamento', registro_id=aproveitamento.pk)
    assert log.acao == AcaoAuditoria.CRIAR
    assert log.usuario == user_secretaria


@pytest.mark.django_db
def test_recusa_aproveitamento_duplicado_mas_permite_apos_indeferimento(
    aproveitamento, user_secretaria, user_coordenacao, user_aluno, calculo1,
):
    dados = dict(usuario=user_secretaria, aluno=user_aluno, disciplina=calculo1,
                 instituicao_origem='UFY', disciplina_origem='Cálculo B', carga_horaria_origem=80)
    with pytest.raises(ValidationError, match='pendente ou deferido'):
        registrar_aproveitamento(**dados)

    analisar_aproveitamento(usuario=user_coordenacao, aproveitamento_id=aproveitamento.pk,
                            decisao=StatusAproveitamento.INDEFERIDO, justificativa='Ementa diferente.')

    assert registrar_aproveitamento(**dados).status == StatusAproveitamento.PENDENTE


@pytest.mark.django_db
def test_recusa_aluno_inativo(user_secretaria, user_aluno, calculo1):
    user_aluno.is_active = False
    user_aluno.save(update_fields=['is_active'])

    with pytest.raises(ValidationError, match='aluno ativo'):
        registrar_aproveitamento(usuario=user_secretaria, aluno=user_aluno, disciplina=calculo1,
                                 instituicao_origem='UFX', disciplina_origem='A', carga_horaria_origem=80)


@pytest.mark.django_db
def test_deferimento_exige_75_por_cento_da_carga(aproveitamento, user_coordenacao):
    # 60h de origem para 80h exigidas: exatamente 75%.
    assert analisar_aproveitamento(
        usuario=user_coordenacao, aproveitamento_id=aproveitamento.pk,
        decisao=StatusAproveitamento.DEFERIDO, justificativa='Ok.',
    ).status == StatusAproveitamento.DEFERIDO


@pytest.mark.django_db
def test_deferimento_recusado_abaixo_de_75_por_cento(user_secretaria, user_coordenacao, user_aluno, calculo1):
    registro = registrar_aproveitamento(usuario=user_secretaria, aluno=user_aluno, disciplina=calculo1,
                                        instituicao_origem='UFX', disciplina_origem='A',
                                        carga_horaria_origem=59)

    with pytest.raises(ValidationError, match='insuficiente'):
        analisar_aproveitamento(usuario=user_coordenacao, aproveitamento_id=registro.pk,
                                decisao=StatusAproveitamento.DEFERIDO, justificativa='Ok.')
    registro.refresh_from_db()
    assert registro.status == StatusAproveitamento.PENDENTE


@pytest.mark.django_db
def test_analise_registra_auditoria_e_nao_aceita_segunda_decisao(aproveitamento, user_coordenacao):
    analisar_aproveitamento(usuario=user_coordenacao, aproveitamento_id=aproveitamento.pk,
                            decisao=StatusAproveitamento.INDEFERIDO, justificativa='Ementa diferente.')

    log = AuditoriaLog.objects.get(tabela_afetada='Aproveitamento', acao=AcaoAuditoria.EDITAR)
    assert 'PENDENTE' in log.valor_antigo and 'INDEFERIDO' in log.valor_novo
    with pytest.raises(ValidationError, match='já foi analisado'):
        analisar_aproveitamento(usuario=user_coordenacao, aproveitamento_id=aproveitamento.pk,
                                decisao=StatusAproveitamento.DEFERIDO, justificativa='Revisto.')


@pytest.mark.django_db
@pytest.mark.parametrize('justificativa', ['', '   ', 'x' * 3001])
def test_analise_exige_justificativa_valida(aproveitamento, user_coordenacao, justificativa):
    with pytest.raises(ValidationError, match='justificativa'):
        analisar_aproveitamento(usuario=user_coordenacao, aproveitamento_id=aproveitamento.pk,
                                decisao=StatusAproveitamento.INDEFERIDO, justificativa=justificativa)


@pytest.mark.django_db
def test_papeis_do_aproveitamento(aproveitamento, user_coordenacao, user_secretaria, user_aluno, calculo2):
    with pytest.raises(PermissionDenied):
        registrar_aproveitamento(usuario=user_coordenacao, aluno=user_aluno, disciplina=calculo2,
                                 instituicao_origem='UFX', disciplina_origem='A', carga_horaria_origem=80)
    with pytest.raises(PermissionDenied):
        analisar_aproveitamento(usuario=user_secretaria, aproveitamento_id=aproveitamento.pk,
                                decisao=StatusAproveitamento.DEFERIDO, justificativa='Ok.')


@pytest.mark.django_db
def test_constraint_exige_analise_coerente(user_secretaria, user_aluno, calculo1):
    with pytest.raises(IntegrityError), transaction.atomic():
        Aproveitamento.objects.create(
            aluno=user_aluno, disciplina=calculo1, instituicao_origem='UFX',
            disciplina_origem='A', carga_horaria_origem=80, registrado_por=user_secretaria,
            status=StatusAproveitamento.DEFERIDO,
        )


# --- Views e RBAC ------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_secretaria', 'user_professor', 'user_aluno'])
def test_tela_de_pre_requisitos_restrita_a_coordenacao(client, request, fixture, calculo1):
    client.force_login(request.getfixturevalue(fixture))

    assert client.get(reverse('academics:pre_requisitos', args=[calculo1.pk])).status_code == 403


@pytest.mark.django_db
def test_coordenacao_adiciona_e_remove_pela_tela(client, user_coordenacao, calculo1, calculo2):
    client.force_login(user_coordenacao)
    url = reverse('academics:pre_requisitos', args=[calculo2.pk])

    resposta = client.post(url, {'requisito': calculo1.pk})
    assert resposta.status_code == 302
    item = PreRequisito.objects.get()

    resposta = client.get(url)
    assert resposta.status_code == 200
    assert 'Cálculo I' in resposta.content.decode()

    assert client.post(reverse('academics:pre_requisito_remover', args=[item.pk])).status_code == 302
    assert not PreRequisito.objects.exists()


@pytest.mark.django_db
def test_tela_nao_oferece_opcao_que_geraria_ciclo_invalido(client, user_coordenacao, calculo1, calculo2):
    adicionar_pre_requisito(usuario=user_coordenacao, disciplina=calculo2, requisito=calculo1)
    client.force_login(user_coordenacao)

    resposta = client.post(reverse('academics:pre_requisitos', args=[calculo1.pk]), {'requisito': calculo2.pk})

    assert resposta.status_code == 200
    assert 'ciclo' in resposta.content.decode()
    assert PreRequisito.objects.count() == 1


@pytest.mark.django_db
def test_aluno_ve_somente_os_proprios_aproveitamentos(client, aproveitamento, user_secretaria, calculo2):
    outro = CustomUser.objects.create_user(email='outro@sga.edu.br', full_name='Outro Aluno',
                                           role=UserRole.ALUNO, password='x', must_change_password=False)
    alheio = registrar_aproveitamento(usuario=user_secretaria, aluno=outro, disciplina=calculo2,
                                      instituicao_origem='UFZ', disciplina_origem='B', carga_horaria_origem=80)
    client.force_login(aproveitamento.aluno)

    lista = client.get(reverse('academics:aproveitamento_index'))
    assert lista.status_code == 200
    assert list(lista.context['page_obj']) == [aproveitamento]
    assert client.get(reverse('academics:aproveitamento_detalhe', args=[aproveitamento.pk])).status_code == 200
    assert client.get(reverse('academics:aproveitamento_detalhe', args=[alheio.pk])).status_code == 404


@pytest.mark.django_db
def test_professor_nao_acessa_aproveitamentos(client, user_professor):
    client.force_login(user_professor)

    assert client.get(reverse('academics:aproveitamento_index')).status_code == 403


@pytest.mark.django_db
def test_filtro_invalido_retorna_400(client, user_secretaria):
    client.force_login(user_secretaria)

    assert client.get(reverse('academics:aproveitamento_index'), {'status': 'X'}).status_code == 400


@pytest.mark.django_db
def test_secretaria_registra_pela_tela(client, user_secretaria, user_aluno, calculo1):
    client.force_login(user_secretaria)

    resposta = client.post(reverse('academics:aproveitamento_criar'), {
        'aluno': user_aluno.pk, 'disciplina': calculo1.pk, 'instituicao_origem': 'UFX',
        'disciplina_origem': 'Cálculo A', 'carga_horaria_origem': 80,
    })

    registro = Aproveitamento.objects.get()
    assert resposta.status_code == 302
    assert resposta.url == reverse('academics:aproveitamento_detalhe', args=[registro.pk])


@pytest.mark.django_db
def test_coordenacao_nao_registra_e_secretaria_nao_analisa_pela_tela(
    client, aproveitamento, user_coordenacao, user_secretaria,
):
    client.force_login(user_coordenacao)
    assert client.get(reverse('academics:aproveitamento_criar')).status_code == 403

    client.force_login(user_secretaria)
    resposta = client.post(reverse('academics:aproveitamento_analisar', args=[aproveitamento.pk]),
                           {'decisao': 'DEFERIDO', 'justificativa': 'Ok.'})
    assert resposta.status_code == 403


@pytest.mark.django_db
def test_coordenacao_analisa_pela_tela(client, aproveitamento, user_coordenacao):
    client.force_login(user_coordenacao)
    url = reverse('academics:aproveitamento_analisar', args=[aproveitamento.pk])

    resposta = client.post(url, {'decisao': 'DEFERIDO', 'justificativa': 'Ementa equivalente.'})

    assert resposta.status_code == 302
    aproveitamento.refresh_from_db()
    assert aproveitamento.status == StatusAproveitamento.DEFERIDO
    assert client.post(url, {'decisao': 'INDEFERIDO', 'justificativa': 'Outra.'}).status_code == 400
