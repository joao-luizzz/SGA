"""
Fixtures compartilhadas para os testes de attendance e auditoria.
Adiciona ao conftest principal: turma, curso, disciplina, matriculas, faltas.
"""
import pytest
from datetime import date
from academics.models import Curso, Disciplina, Turma
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def curso(db):
    return Curso.objects.create(nome='ADS', codigo='ADS001', ativo=True)


@pytest.fixture
def disciplina(db, curso):
    return Disciplina.objects.create(
        nome='Programação Orientada a Objetos',
        codigo='POO001',
        carga_horaria=80,
        curso=curso,
        ativo=True,
    )


@pytest.fixture
def turma(db, disciplina, user_professor):
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/1',
        horarios='SEG 08:00-10:00',
        sala='Lab 01',
        vagas_maximas=30,
        professor=user_professor,
        ativo=True,
    )


@pytest.fixture
def matricula_aluno(db, turma, user_aluno):
    return Matricula.objects.create(
        aluno=user_aluno,
        turma=turma,
        status=StatusMatricula.ATIVA,
    )


@pytest.fixture
def data_aula():
    return date(2026, 8, 10)
