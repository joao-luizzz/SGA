import csv
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from academics.models import Curso, Disciplina, Turma
from academics.selectors import get_relatorio_turmas
from assessments.models import Nota, TipoAvaliacao
from assessments.selectors import SituacaoAcademica
from attendance.models import Falta
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def dados_relatorio(db, user_professor, user_aluno):
    curso_ads = Curso.objects.create(nome='ADS', codigo='ADS-REL')
    curso_si = Curso.objects.create(nome='Sistemas de Informação', codigo='SI-REL')
    disciplina_ads = Disciplina.objects.create(
        nome='Relatórios', codigo='REL-01', carga_horaria=40, curso=curso_ads
    )
    disciplina_si = Disciplina.objects.create(
        nome='Banco de Dados', codigo='BD-01', carga_horaria=40, curso=curso_si
    )
    turma_ads_1 = Turma.objects.create(
        disciplina=disciplina_ads,
        periodo_letivo='2026/1',
        horarios='SEG 19:00-21:00',
        vagas_maximas=2,
        professor=user_professor,
    )
    turma_ads_2 = Turma.objects.create(
        disciplina=disciplina_ads,
        periodo_letivo='2026/2',
        horarios='TER 19:00-21:00',
        vagas_maximas=2,
        professor=user_professor,
    )
    turma_si = Turma.objects.create(
        disciplina=disciplina_si,
        periodo_letivo='2026/2',
        horarios='QUA 19:00-21:00',
        vagas_maximas=2,
        professor=user_professor,
    )
    matricula = Matricula.objects.create(
        turma=turma_ads_1,
        aluno=user_aluno,
        status=StatusMatricula.ATIVA,
    )
    return {
        'curso_ads': curso_ads,
        'curso_si': curso_si,
        'turma_ads_1': turma_ads_1,
        'turma_ads_2': turma_ads_2,
        'turma_si': turma_si,
        'matricula': matricula,
    }


def _ids_turmas(relatorio):
    return {turma.pk for turma in relatorio['turmas']}


def _criar_aluno(numero):
    return get_user_model().objects.create_user(
        email=f'aluno.relatorio{numero}@sga.edu.br',
        full_name=f'Aluno Relatório {numero}',
        role='ALUNO',
        password='senha',
    )


def _criar_notas(matricula, professor, valores):
    for tipo, valor in valores.items():
        Nota.objects.create(
            matricula=matricula,
            tipo=tipo,
            valor=Decimal(valor),
            registrado_por=professor,
        )


@pytest.mark.django_db
def test_relatorio_considera_apenas_matriculas_ativas(dados_relatorio):
    outro_aluno = _criar_aluno(1)
    Matricula.objects.create(
        turma=dados_relatorio['turma_ads_1'],
        aluno=outro_aluno,
        status=StatusMatricula.CANCELADA,
    )

    relatorio = get_relatorio_turmas(turma_id=dados_relatorio['turma_ads_1'].pk)

    assert relatorio['turmas'][0].matriculas_ativas == 1
    assert len(relatorio['linhas']) == 1
    assert relatorio['linhas'][0]['matricula'] == dados_relatorio['matricula']


@pytest.mark.django_db
def test_relatorio_evitar_n_mais_um_de_frequencia(
    dados_relatorio, django_assert_num_queries
):
    for numero in range(2, 5):
        Matricula.objects.create(
            turma=dados_relatorio['turma_ads_1'],
            aluno=_criar_aluno(numero),
            status=StatusMatricula.ATIVA,
        )

    with django_assert_num_queries(4):
        relatorio = get_relatorio_turmas(turma_id=dados_relatorio['turma_ads_1'].pk)

    assert len(relatorio['linhas']) == 4


@pytest.mark.django_db
def test_filtro_por_curso_altera_turmas(dados_relatorio):
    relatorio = get_relatorio_turmas(curso_id=dados_relatorio['curso_ads'].pk)

    assert _ids_turmas(relatorio) == {
        dados_relatorio['turma_ads_1'].pk,
        dados_relatorio['turma_ads_2'].pk,
    }


@pytest.mark.django_db
def test_filtro_por_periodo_altera_turmas(dados_relatorio):
    relatorio = get_relatorio_turmas(periodo='2026/1')

    assert _ids_turmas(relatorio) == {dados_relatorio['turma_ads_1'].pk}


@pytest.mark.django_db
def test_filtro_por_turma_altera_turmas(dados_relatorio):
    relatorio = get_relatorio_turmas(turma_id=dados_relatorio['turma_si'].pk)

    assert _ids_turmas(relatorio) == {dados_relatorio['turma_si'].pk}


@pytest.mark.django_db
def test_filtros_combinados_alteram_turmas(dados_relatorio):
    relatorio = get_relatorio_turmas(
        curso_id=dados_relatorio['curso_ads'].pk,
        periodo='2026/2',
    )

    assert _ids_turmas(relatorio) == {dados_relatorio['turma_ads_2'].pk}


@pytest.mark.django_db
def test_coordenacao_acessa_relatorios_html(
    client, user_coordenacao, password, dados_relatorio
):
    client.login(username=user_coordenacao.email, password=password)

    response = client.get(reverse('academics:relatorios'))

    assert response.status_code == 200
    assert dados_relatorio['turma_ads_1'] in response.context['turmas']


@pytest.mark.django_db
@pytest.mark.parametrize('role_fixture', ['user_aluno', 'user_professor', 'user_secretaria'])
@pytest.mark.parametrize('url_name', ['academics:relatorios', 'academics:relatorios_csv'])
def test_relatorios_restritos_a_coordenacao(
    client, request, role_fixture, url_name, password
):
    user = request.getfixturevalue(role_fixture)
    client.login(username=user.email, password=password)

    response = client.get(reverse(url_name))

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('url_name', ['academics:relatorios', 'academics:relatorios_csv'])
def test_relatorios_redirecionam_usuario_anonimo_para_login(client, url_name):
    url = reverse(url_name)

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('accounts:login')}?next={url}"


@pytest.mark.django_db
def test_csv_exporta_dados_academicos_corretos(
    client, user_coordenacao, user_professor, password, dados_relatorio
):
    matricula = dados_relatorio['matricula']
    _criar_notas(
        matricula,
        user_professor,
        {
            TipoAvaliacao.P1: '5.00',
            TipoAvaliacao.P2: '5.00',
            TipoAvaliacao.TRABALHO: '5.00',
            TipoAvaliacao.EXAME: '7.00',
        },
    )
    for deslocamento, presente in enumerate([True, True, True, False]):
        Falta.objects.create(
            turma=dados_relatorio['turma_ads_1'],
            aluno=matricula.aluno,
            data_aula=date(2026, 8, 3) + timedelta(days=deslocamento),
            presente=presente,
            registrado_por=user_professor,
        )
    client.login(username=user_coordenacao.email, password=password)

    response = client.get(
        reverse('academics:relatorios_csv'),
        {'turma': dados_relatorio['turma_ads_1'].pk},
    )

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    assert 'attachment' in response['Content-Disposition']
    assert 'relatorio-academico.csv' in response['Content-Disposition']
    linhas = list(csv.reader(StringIO(response.content.decode('utf-8-sig'))))
    assert linhas[0] == [
        'Turma', 'Curso', 'Periodo', 'Aluno', 'Matricula',
        'Vagas maximas', 'Matriculados ativos', 'Vagas disponiveis',
        'P1', 'P2', 'Trabalho', 'Exame', 'Media parcial', 'Media final',
        'Situacao', 'Frequencia (%)', 'Faltas',
    ]
    assert linhas[1] == [
        'Relatórios',
        'ADS',
        '2026/1',
        matricula.aluno.full_name,
        str(matricula.pk),
        '2',
        '1',
        '1',
        '5.00',
        '5.00',
        '5.00',
        '7.00',
        '5.00',
        '6.00',
        SituacaoAcademica.APROVADO_EXAME,
        '75.0',
        '1',
    ]


@pytest.mark.django_db
def test_relatorio_cobre_situacoes_academicas(user_professor):
    curso = Curso.objects.create(nome='Situações', codigo='SIT-REL')
    disciplina = Disciplina.objects.create(
        nome='Resultados', codigo='RES-REL', carga_horaria=40, curso=curso
    )
    turma = Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/2',
        horarios='SEG 19:00-21:00',
        vagas_maximas=10,
        professor=user_professor,
    )
    cenarios = [
        ({TipoAvaliacao.P1: '7.00'}, SituacaoAcademica.EM_ANDAMENTO),
        (
            {
                TipoAvaliacao.P1: '6.00',
                TipoAvaliacao.P2: '6.00',
                TipoAvaliacao.TRABALHO: '6.00',
            },
            SituacaoAcademica.APROVADO_DIRETO,
        ),
        (
            {
                TipoAvaliacao.P1: '5.00',
                TipoAvaliacao.P2: '5.00',
                TipoAvaliacao.TRABALHO: '5.00',
            },
            SituacaoAcademica.ELEGIVEL_EXAME,
        ),
        (
            {
                TipoAvaliacao.P1: '5.00',
                TipoAvaliacao.P2: '5.00',
                TipoAvaliacao.TRABALHO: '5.00',
                TipoAvaliacao.EXAME: '7.00',
            },
            SituacaoAcademica.APROVADO_EXAME,
        ),
        (
            {
                TipoAvaliacao.P1: '3.00',
                TipoAvaliacao.P2: '3.00',
                TipoAvaliacao.TRABALHO: '3.00',
            },
            SituacaoAcademica.REPROVADO_NOTA,
        ),
        (
            {
                TipoAvaliacao.P1: '8.00',
                TipoAvaliacao.P2: '8.00',
                TipoAvaliacao.TRABALHO: '8.00',
            },
            SituacaoAcademica.REPROVADO_FALTA,
        ),
    ]
    situacoes_esperadas = {}
    for numero, (notas, situacao) in enumerate(cenarios, start=10):
        matricula = Matricula.objects.create(
            turma=turma,
            aluno=_criar_aluno(numero),
            status=StatusMatricula.ATIVA,
        )
        _criar_notas(matricula, user_professor, notas)
        situacoes_esperadas[matricula.pk] = situacao
        if situacao == SituacaoAcademica.REPROVADO_FALTA:
            for deslocamento, presente in enumerate([True, True, False, False]):
                Falta.objects.create(
                    turma=turma,
                    aluno=matricula.aluno,
                    data_aula=date(2026, 9, 1) + timedelta(days=deslocamento),
                    presente=presente,
                    registrado_por=user_professor,
                )

    relatorio = get_relatorio_turmas(turma_id=turma.pk)

    assert {
        linha['matricula'].pk: linha['resultado']['situacao']
        for linha in relatorio['linhas']
    } == situacoes_esperadas


@pytest.mark.django_db
def test_relatorio_sem_turmas_para_filtros_retorna_vazio(dados_relatorio):
    relatorio = get_relatorio_turmas(periodo='2099/1')

    assert relatorio['turmas'] == []
    assert relatorio['linhas'] == []


@pytest.mark.django_db
def test_csv_sem_resultados_contem_apenas_cabecalho(
    client, user_coordenacao, password, dados_relatorio
):
    client.login(username=user_coordenacao.email, password=password)

    response = client.get(
        reverse('academics:relatorios_csv'),
        {'periodo': '2099/1'},
    )

    linhas = list(csv.reader(StringIO(response.content.decode('utf-8-sig'))))
    assert response.status_code == 200
    assert len(linhas) == 1
    assert linhas[0][0:5] == ['Turma', 'Curso', 'Periodo', 'Aluno', 'Matricula']


@pytest.mark.django_db
def test_relatorio_sem_matriculas_ativas_nao_cria_linhas(dados_relatorio):
    dados_relatorio['matricula'].status = StatusMatricula.CANCELADA
    dados_relatorio['matricula'].save(update_fields=['status'])

    relatorio = get_relatorio_turmas(turma_id=dados_relatorio['turma_ads_1'].pk)

    assert len(relatorio['turmas']) == 1
    assert relatorio['linhas'] == []


@pytest.mark.django_db
def test_pagina_exibe_estado_vazio_para_turma_sem_matriculas_ativas(
    client, user_coordenacao, password, dados_relatorio
):
    dados_relatorio['matricula'].status = StatusMatricula.CANCELADA
    dados_relatorio['matricula'].save(update_fields=['status'])
    client.login(username=user_coordenacao.email, password=password)

    response = client.get(
        reverse('academics:relatorios'),
        {'turma': dados_relatorio['turma_ads_1'].pk},
    )

    assert response.status_code == 200
    assert 'Nenhum aluno matriculado ativamente.' in response.content.decode()
