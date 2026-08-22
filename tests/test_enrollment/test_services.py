import pytest
from django.core.exceptions import ValidationError
from apps.enrollment.models import Matricula, StatusMatricula
from apps.enrollment.services import matricular_aluno_administrativo
from apps.accounts.models import CustomUser, UserRole
from apps.academics.models import Turma, Curso, Disciplina

@pytest.fixture
def secretaria(db):
    return CustomUser.objects.create(email='sec@test.com', full_name='Secretaria Teste', role=UserRole.SECRETARIA)

@pytest.fixture
def aluno(db):
    return CustomUser.objects.create(email='aluno@test.com', full_name='Aluno Teste', role=UserRole.ALUNO)

@pytest.fixture
def professor(db):
    return CustomUser.objects.create(email='prof@test.com', full_name='Professor Teste', role=UserRole.PROFESSOR)

@pytest.fixture
def turma(db, professor):
    curso = Curso.objects.create(nome='Curso', codigo='C1')
    disciplina = Disciplina.objects.create(nome='Disciplina', codigo='D1', carga_horaria=40, curso=curso)
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026.1',
        horarios='SEG 08:00-10:00',
        vagas_maximas=2,
        professor=professor
    )

@pytest.mark.django_db
def test_matricular_aluno_administrativo_sucesso(secretaria, aluno, turma):
    matricula = matricular_aluno_administrativo(secretaria, aluno, turma)
    
    assert matricula.status == StatusMatricula.ATIVA
    assert matricula.aluno == aluno
    assert matricula.turma == turma
    assert turma.vagas_ocupadas == 1

@pytest.mark.django_db
def test_matricular_apenas_secretaria(aluno, professor, turma):
    # Professor tenta matricular
    with pytest.raises(ValidationError, match="perfil de Secretaria"):
        matricular_aluno_administrativo(professor, aluno, turma)

    # Aluno tenta matricular ele mesmo
    with pytest.raises(ValidationError, match="perfil de Secretaria"):
        matricular_aluno_administrativo(aluno, aluno, turma)

@pytest.mark.django_db
def test_matricular_somente_aluno(secretaria, professor, turma):
    with pytest.raises(ValidationError, match="perfil de ALUNO"):
        matricular_aluno_administrativo(secretaria, professor, turma)

@pytest.mark.django_db
def test_matricular_limite_vagas_service(secretaria, aluno, turma):
    aluno2 = CustomUser.objects.create(email='aluno2@test.com', full_name='Aluno 2', role=UserRole.ALUNO)
    aluno3 = CustomUser.objects.create(email='aluno3@test.com', full_name='Aluno 3', role=UserRole.ALUNO)

    # Ocupa as 2 vagas
    matricular_aluno_administrativo(secretaria, aluno, turma)
    matricular_aluno_administrativo(secretaria, aluno2, turma)

    assert turma.vagas_disponiveis == 0

    # Tenta matricular o 3o aluno
    with pytest.raises(ValidationError, match="não possui vagas disponíveis"):
        matricular_aluno_administrativo(secretaria, aluno3, turma)

@pytest.mark.django_db
def test_matricular_reativacao(secretaria, aluno, turma):
    # Matricula e depois cancela
    matricula = matricular_aluno_administrativo(secretaria, aluno, turma)
    matricula.status = StatusMatricula.CANCELADA
    matricula.save()

    assert turma.vagas_ocupadas == 0

    # Tenta matricular novamente
    matricula_reativada = matricular_aluno_administrativo(secretaria, aluno, turma)
    
    # Verifica se reativou a mesma matrícula
    assert matricula_reativada.pk == matricula.pk
    assert matricula_reativada.status == StatusMatricula.ATIVA
    assert turma.vagas_ocupadas == 1
