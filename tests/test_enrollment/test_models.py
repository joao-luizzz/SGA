import pytest
from django.db import IntegrityError
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def curso(db):
    return Curso.objects.create(nome='ADS', codigo='ADS001', ativo=True)


@pytest.fixture
def disciplina(db, curso):
    return Disciplina.objects.create(
        nome='Banco de Dados',
        codigo='BD001',
        carga_horaria=60,
        curso=curso,
        ativo=True,
    )


@pytest.fixture
def turma(db, disciplina, user_professor):
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/1',
        horarios='QUA 08:00-10:00',
        sala='Sala 101',
        vagas_maximas=30,
        professor=user_professor,
        ativo=True,
    )


@pytest.mark.django_db
class TestMatriculaModel:

    def test_criar_matricula_sucesso(self, user_aluno, turma):
        matricula = Matricula.objects.create(
            aluno=user_aluno,
            turma=turma,
            status=StatusMatricula.ATIVA,
        )
        assert matricula.pk is not None
        assert matricula.esta_ativa is True
        assert str(matricula) == f"{user_aluno.full_name} → {turma} [Ativa]"

    def test_matricula_duplicada_levanta_integrity_error(self, user_aluno, turma):
        Matricula.objects.create(
            aluno=user_aluno,
            turma=turma,
            status=StatusMatricula.ATIVA,
        )
        with pytest.raises(IntegrityError):
            Matricula.objects.create(
                aluno=user_aluno,
                turma=turma,
                status=StatusMatricula.ATIVA,
            )

    def test_status_matricula_nao_ativa(self, user_aluno, turma):
        matricula = Matricula.objects.create(
            aluno=user_aluno,
            turma=turma,
            status=StatusMatricula.TRANCADA,
        )
        assert matricula.esta_ativa is False
        assert "Trancada" in str(matricula)
