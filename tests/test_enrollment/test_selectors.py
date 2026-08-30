import pytest
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from enrollment.models import Matricula, StatusMatricula
from enrollment.selectors import (
    get_matriculas_ativas_da_turma,
    get_matriculas_do_aluno,
    contar_vagas_ocupadas,
    turma_pode_receber_matricula,
    aluno_ja_matriculado,
)


@pytest.fixture
def curso(db):
    return Curso.objects.create(nome='ADS', codigo='ADS001', ativo=True)


@pytest.fixture
def disciplina(db, curso):
    return Disciplina.objects.create(
        nome='Engenharia de Software',
        codigo='ES001',
        carga_horaria=60,
        curso=curso,
        ativo=True,
    )


@pytest.fixture
def turma(db, disciplina, user_professor):
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/1',
        horarios='QUI 08:00-10:00',
        sala='Sala 202',
        vagas_maximas=2,
        professor=user_professor,
        ativo=True,
    )


@pytest.mark.django_db
class TestEnrollmentSelectors:

    def test_get_matriculas_ativas_da_turma(self, turma, user_aluno):
        m1 = Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        aluno2 = CustomUser.objects.create_user(
            email='aluno2@sga.edu.br',
            full_name='Aluno 2',
            role=UserRole.ALUNO,
            password='SenhaSegura123!',
        )
        Matricula.objects.create(aluno=aluno2, turma=turma, status=StatusMatricula.CANCELADA)

        ativas = get_matriculas_ativas_da_turma(turma)
        assert list(ativas) == [m1]

    def test_get_matriculas_do_aluno(self, turma, user_aluno):
        m = Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        matriculas = get_matriculas_do_aluno(user_aluno)
        assert list(matriculas) == [m]

    def test_contar_vagas_ocupadas(self, turma, user_aluno):
        assert contar_vagas_ocupadas(turma) == 0
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        assert contar_vagas_ocupadas(turma) == 1

    def test_turma_pode_receber_matricula(self, turma, user_aluno):
        assert turma_pode_receber_matricula(turma) is True
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        assert turma_pode_receber_matricula(turma) is True

        aluno2 = CustomUser.objects.create_user(
            email='aluno2@sga.edu.br',
            full_name='Aluno 2',
            role=UserRole.ALUNO,
            password='SenhaSegura123!',
        )
        Matricula.objects.create(aluno=aluno2, turma=turma, status=StatusMatricula.ATIVA)
        assert turma_pode_receber_matricula(turma) is False

    def test_aluno_ja_matriculado(self, turma, user_aluno):
        assert aluno_ja_matriculado(user_aluno, turma) is False
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        assert aluno_ja_matriculado(user_aluno, turma) is True

    @pytest.mark.parametrize(
        'status',
        [StatusMatricula.CANCELADA, StatusMatricula.TRANCADA],
    )
    def test_matricula_inativa_nao_bloqueia_nova_tentativa(
        self, turma, user_aluno, status
    ):
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=status)
        assert aluno_ja_matriculado(user_aluno, turma) is False
