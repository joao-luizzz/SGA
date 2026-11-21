import pytest

from academics.models import Curso, Disciplina, Turma
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def curso_assessments(db):
    return Curso.objects.create(nome='ADS', codigo='ADS-ASSESS', ativo=True)


@pytest.fixture
def disciplina_assessments(db, curso_assessments):
    return Disciplina.objects.create(
        nome='Engenharia de Software',
        codigo='ES-ASSESS',
        carga_horaria=80,
        curso=curso_assessments,
        ativo=True,
    )


@pytest.fixture
def turma_assessments(db, disciplina_assessments, user_professor):
    return Turma.objects.create(
        disciplina=disciplina_assessments,
        periodo_letivo='2026/2',
        horarios='SEG 19:00-21:00',
        sala='Lab 01',
        vagas_maximas=30,
        professor=user_professor,
        ativo=True,
    )


@pytest.fixture
def matricula_assessments(db, turma_assessments, user_aluno):
    return Matricula.objects.create(
        aluno=user_aluno,
        turma=turma_assessments,
        status=StatusMatricula.ATIVA,
    )
