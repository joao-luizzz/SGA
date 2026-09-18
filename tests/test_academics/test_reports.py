import pytest
from django.urls import reverse

from academics.models import Curso, Disciplina, Turma
from academics.selectors import get_relatorio_turmas
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def turma_relatorio(db, user_professor):
    curso = Curso.objects.create(nome='ADS', codigo='ADS-REL')
    disciplina = Disciplina.objects.create(
        nome='Relatórios', codigo='REL-01', carga_horaria=40, curso=curso
    )
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/2',
        horarios='SEG 19:00-21:00',
        vagas_maximas=2,
        professor=user_professor,
    )


@pytest.mark.django_db
def test_relatorio_considera_apenas_matriculas_ativas(turma_relatorio, user_aluno):
    Matricula.objects.create(
        turma=turma_relatorio, aluno=user_aluno, status=StatusMatricula.ATIVA
    )
    outro_aluno = type(user_aluno).objects.create_user(
        email='outro@sga.edu.br', full_name='Outro Aluno', role='ALUNO', password='senha'
    )
    Matricula.objects.create(
        turma=turma_relatorio, aluno=outro_aluno, status=StatusMatricula.CANCELADA
    )

    relatorio = get_relatorio_turmas(periodo='2026/2')

    assert relatorio['turmas'][0].matriculas_ativas == 1
    assert len(relatorio['linhas']) == 1
    assert relatorio['linhas'][0]['aluno'] == user_aluno


@pytest.mark.django_db
def test_relatorio_filtra_por_curso_e_exporta_csv(
    client, user_coordenacao, password, turma_relatorio, user_aluno
):
    Matricula.objects.create(
        turma=turma_relatorio, aluno=user_aluno, status=StatusMatricula.ATIVA
    )
    client.login(username=user_coordenacao.email, password=password)

    response = client.get(
        reverse('academics:relatorios_csv'),
        {'curso': turma_relatorio.disciplina.curso_id},
    )

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    assert 'relatorio-academico.csv' in response['Content-Disposition']
    assert 'Relatórios' in response.content.decode('utf-8-sig')


@pytest.mark.django_db
@pytest.mark.parametrize('role_fixture', ['user_aluno', 'user_professor', 'user_secretaria'])
def test_relatorios_restritos_a_coordenacao(client, request, role_fixture, password):
    user = request.getfixturevalue(role_fixture)
    client.login(username=user.email, password=password)

    response = client.get(reverse('academics:relatorios'))

    assert response.status_code == 403