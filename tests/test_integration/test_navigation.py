import pytest
from django.urls import reverse

from academics.models import Curso, Disciplina, Turma
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def turma_navegacao(db, user_professor):
    curso = Curso.objects.create(nome='Sistemas de Informação', codigo='SI-NAV', ativo=True)
    disciplina = Disciplina.objects.create(
        curso=curso,
        nome='Navegação Web',
        codigo='NAV-101',
        carga_horaria=60,
        ativo=True,
    )
    return Turma.objects.create(
        disciplina=disciplina,
        professor=user_professor,
        periodo_letivo='2026/2',
        horarios='SEG 19:00-21:00',
        sala='Sala 01',
        vagas_maximas=30,
        ativo=True,
    )


@pytest.mark.django_db
def test_secretaria_acessa_gestao_de_usuarios_e_cards_corretos(client, user_secretaria):
    client.force_login(user_secretaria)

    response = client.get(reverse('accounts:usuario_list'))

    assert response.status_code == 200

    dashboard = client.get(reverse('accounts:dashboard_secretaria'))
    assert dashboard.status_code == 200
    assert (
        f'href="{reverse("accounts:usuario_list")}" '
        'class="btn btn-outline-primary btn-sm w-100"'
    ).encode() in dashboard.content
    assert (
        f'href="{reverse("enrollment:matricula_create")}" '
        'class="btn btn-outline-secondary btn-sm w-100"'
    ).encode() in dashboard.content


@pytest.mark.django_db
def test_professor_acessa_avaliacoes_e_ve_turmas_e_card_corretos(
    client, user_professor, turma_navegacao
):
    client.force_login(user_professor)

    response = client.get(reverse('assessments:index'))

    assert response.status_code == 200
    assert turma_navegacao.disciplina.nome.encode() in response.content
    assert 'Lançar notas'.encode() in response.content

    dashboard = client.get(reverse('accounts:dashboard_professor'))
    assert dashboard.status_code == 200
    assert (
        f'href="{reverse("assessments:index")}" '
        'class="btn btn-success btn-sm w-100 shadow-sm"'
    ).encode() in dashboard.content


@pytest.mark.django_db
def test_aluno_acessa_boletim_e_card_correto(
    client, user_aluno, turma_navegacao
):
    Matricula.objects.create(
        aluno=user_aluno,
        turma=turma_navegacao,
        status=StatusMatricula.ATIVA,
    )
    client.force_login(user_aluno)

    response = client.get(reverse('assessments:index'))

    assert response.status_code == 200
    assert b'Meu Boletim' in response.content
    assert turma_navegacao.disciplina.nome.encode() in response.content

    dashboard = client.get(reverse('accounts:dashboard_aluno'))
    assert dashboard.status_code == 200
    assert (
        f'href="{reverse("assessments:index")}" '
        'class="btn btn-outline-success btn-sm w-100"'
    ).encode() in dashboard.content
