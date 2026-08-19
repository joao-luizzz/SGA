import pytest
from django.urls import reverse
from academics.models import Curso, Disciplina, Turma
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def curso(db):
    return Curso.objects.create(nome='ADS', codigo='ADS001', ativo=True)


@pytest.fixture
def disciplina(db, curso):
    return Disciplina.objects.create(
        nome='Arquitetura de Software',
        codigo='AS001',
        carga_horaria=60,
        curso=curso,
        ativo=True,
    )


@pytest.fixture
def turma(db, disciplina, user_professor):
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/1',
        horarios='SEX 08:00-10:00',
        sala='Sala 303',
        vagas_maximas=30,
        professor=user_professor,
        ativo=True,
    )


@pytest.mark.django_db
class TestEnrollmentViews:

    def test_aluno_acessa_minhas_matriculas(self, client, user_aluno, turma, password):
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        client.login(username=user_aluno.email, password=password)
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 200
        assert turma.disciplina.nome.encode() in response.content

    def test_secretaria_acessa_gestao_matriculas(self, client, user_secretaria, password):
        client.login(username=user_secretaria.email, password=password)
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 200

    def test_professor_bloqueado_em_matriculas(self, client, user_professor, password):
        client.login(username=user_professor.email, password=password)
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 403

    def test_anonimo_redirecionado_login(self, client):
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/' in response['Location']
