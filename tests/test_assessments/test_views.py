from decimal import Decimal

import pytest
from django.urls import reverse

from accounts.models import CustomUser, UserRole
from assessments.models import Nota, TipoAvaliacao
from enrollment.models import Matricula, StatusMatricula


@pytest.mark.django_db
def test_professor_ve_apenas_suas_turmas(
    client, user_professor, turma_assessments, disciplina_assessments, password
):
    outro_professor = CustomUser.objects.create_user(
        email='outro.view@sga.edu.br', full_name='Outro Professor',
        role=UserRole.PROFESSOR, password=password,
    )
    turma_alheia = type(turma_assessments).objects.create(
        disciplina=disciplina_assessments, periodo_letivo='2026/1',
        horarios='TER 19:00-21:00', sala='Lab 02', vagas_maximas=30,
        professor=outro_professor, ativo=True,
    )
    client.login(username=user_professor.email, password=password)
    response = client.get(reverse('assessments:index'))
    assert response.status_code == 200
    assert list(response.context['turmas']) == [turma_assessments]
    assert client.get(reverse('assessments:turma_notas', args=[turma_alheia.pk])).status_code == 404


@pytest.mark.django_db
def test_aluno_ve_somente_o_proprio_boletim(
    client, user_aluno, user_professor, turma_assessments,
    matricula_assessments, password
):
    outro_aluno = CustomUser.objects.create_user(
        email='colega@sga.edu.br', full_name='Colega Secreto',
        role=UserRole.ALUNO, password=password,
    )
    outra_matricula = Matricula.objects.create(
        aluno=outro_aluno, turma=turma_assessments, status=StatusMatricula.ATIVA,
    )
    Nota.objects.create(
        matricula=outra_matricula, tipo=TipoAvaliacao.P1,
        valor=Decimal('10.00'), registrado_por=user_professor,
    )
    client.login(username=user_aluno.email, password=password)
    response = client.get(reverse('assessments:index'))
    assert response.status_code == 200
    assert len(response.context['boletim']) == 1
    assert response.context['boletim'][0]['matricula'] == matricula_assessments
    assert b'Colega Secreto' not in response.content


@pytest.mark.django_db
def test_aluno_nao_acessa_lancamento(
    client, user_aluno, turma_assessments, password
):
    client.login(username=user_aluno.email, password=password)
    response = client.get(reverse('assessments:turma_notas', args=[turma_assessments.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_professor_lanca_notas_pela_tela(
    client, user_professor, turma_assessments, matricula_assessments, password
):
    client.login(username=user_professor.email, password=password)
    response = client.post(
        reverse('assessments:turma_notas', args=[turma_assessments.pk]),
        {
            f'nota_{matricula_assessments.pk}_P1': '8.00',
            f'nota_{matricula_assessments.pk}_P2': '7.00',
            f'nota_{matricula_assessments.pk}_TRABALHO': '9.00',
            f'nota_{matricula_assessments.pk}_EXAME': '',
        },
    )
    assert response.status_code == 302
    assert Nota.objects.filter(matricula=matricula_assessments).count() == 3
