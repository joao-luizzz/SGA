from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from attendance.models import Falta
from attendance.selectors import get_frequencia_do_aluno_na_turma
from enrollment.models import Matricula, StatusMatricula
from enrollment.services import (
    alterar_status_matricula_administrativa,
    matricular_aluno_administrativo,
)


@pytest.fixture
def turma_valida(db, user_professor):
    curso = Curso.objects.create(nome='Curso', codigo='MAT-ADM')
    disciplina = Disciplina.objects.create(
        nome='Disciplina',
        codigo='MAT-ADM',
        carga_horaria=40,
        curso=curso,
    )
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/1',
        horarios='SEG 08:00-10:00',
        sala='Sala 1',
        vagas_maximas=2,
        professor=user_professor,
        ativo=True,
    )


@pytest.mark.django_db
def test_matricula_administrativa_valida_bloqueia_turma(
    user_secretaria, user_aluno, turma_valida
):
    with patch.object(
        Turma.objects,
        'select_for_update',
        wraps=Turma.objects.select_for_update,
    ) as select_for_update:
        matricula = matricular_aluno_administrativo(
            user_secretaria, user_aluno, turma_valida
        )

    select_for_update.assert_called_once_with()
    assert matricula.status == StatusMatricula.ATIVA
    assert matricula.aluno == user_aluno
    assert matricula.turma == turma_valida


@pytest.mark.django_db
def test_apenas_secretaria_pode_matricular(user_professor, user_aluno, turma_valida):
    with pytest.raises(ValidationError, match='perfil de Secretaria'):
        matricular_aluno_administrativo(user_professor, user_aluno, turma_valida)


@pytest.mark.django_db
def test_aluno_precisa_estar_ativo(user_secretaria, user_aluno, turma_valida):
    user_aluno.is_active = False
    user_aluno.save(update_fields=['is_active'])

    with pytest.raises(ValidationError, match='estar ativo'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, turma_valida)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('campo', 'valor'),
    [
        ('professor', None),
        ('horarios', ''),
        ('sala', ''),
        ('vagas_maximas', 0),
    ],
)
def test_turma_incompleta_nao_aceita_matricula(
    user_secretaria, user_aluno, turma_valida, campo, valor
):
    setattr(turma_valida, campo, valor)
    turma_valida.save(update_fields=[campo])

    with pytest.raises(ValidationError, match='professor, horário, sala e vagas'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, turma_valida)


@pytest.mark.django_db
def test_nao_permite_exceder_vagas(user_secretaria, user_aluno, turma_valida):
    turma_valida.vagas_maximas = 1
    turma_valida.save(update_fields=['vagas_maximas'])
    outro_aluno = CustomUser.objects.create_user(
        email='outro.aluno@sga.edu.br',
        full_name='Outro Aluno',
        role=UserRole.ALUNO,
        password='SenhaSegura123!',
    )
    Matricula.objects.create(aluno=outro_aluno, turma=turma_valida)

    with pytest.raises(ValidationError, match='não possui vagas'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, turma_valida)


@pytest.mark.django_db
def test_nao_permite_duplicidade_ativa(user_secretaria, user_aluno, turma_valida):
    Matricula.objects.create(aluno=user_aluno, turma=turma_valida)

    with pytest.raises(ValidationError, match='matrícula ativa'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, turma_valida)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'status_anterior',
    [StatusMatricula.CANCELADA, StatusMatricula.TRANCADA, StatusMatricula.CONCLUIDA],
)
def test_rematricula_na_mesma_turma_e_rejeitada_mesmo_com_historico_encerrado(
    user_secretaria, user_aluno, turma_valida, status_anterior
):
    Matricula.objects.create(
        aluno=user_aluno,
        turma=turma_valida,
        status=status_anterior,
    )

    with pytest.raises(ValidationError, match='outra turma/período'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, turma_valida)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'status_anterior', [StatusMatricula.CANCELADA, StatusMatricula.TRANCADA]
)
def test_rematricula_em_outra_turma_preserva_historico_e_frequencia(
    user_secretaria, user_aluno, user_professor, turma_valida, status_anterior
):
    matricula_anterior = Matricula.objects.create(
        aluno=user_aluno,
        turma=turma_valida,
        status=StatusMatricula.ATIVA,
    )
    Falta.objects.create(
        turma=turma_valida,
        aluno=user_aluno,
        data_aula='2026-08-18',
        presente=False,
        registrado_por=user_professor,
    )
    matricula_anterior.status = status_anterior
    matricula_anterior.save(update_fields=['status'])
    turma_nova = Turma.objects.create(
        disciplina=turma_valida.disciplina,
        periodo_letivo='2026/2',
        horarios='TER 08:00-10:00',
        sala='Sala 2',
        vagas_maximas=2,
        professor=user_professor,
        ativo=True,
    )

    nova_matricula = matricular_aluno_administrativo(
        user_secretaria, user_aluno, turma_nova
    )

    assert nova_matricula.status == StatusMatricula.ATIVA
    assert matricula_anterior.status == status_anterior
    assert Falta.objects.filter(aluno=user_aluno, turma=turma_valida).count() == 1
    assert Falta.objects.filter(aluno=user_aluno, turma=turma_nova).count() == 0
    assert get_frequencia_do_aluno_na_turma(user_aluno, turma_nova)['total_aulas'] == 0


@pytest.mark.django_db
def test_alterar_status_bloqueia_matricula_e_preserva_status_encerrado(
    user_secretaria, user_aluno, turma_valida
):
    matricula = Matricula.objects.create(aluno=user_aluno, turma=turma_valida)

    with patch.object(
        Matricula.objects,
        'select_for_update',
        wraps=Matricula.objects.select_for_update,
    ) as select_for_update:
        alterar_status_matricula_administrativa(
            user_secretaria, matricula.pk, StatusMatricula.TRANCADA
        )

    select_for_update.assert_called_once_with()
    matricula.refresh_from_db()
    assert matricula.status == StatusMatricula.TRANCADA
    with pytest.raises(ValidationError, match='matrículas ativas'):
        alterar_status_matricula_administrativa(
            user_secretaria, matricula.pk, StatusMatricula.CANCELADA
        )
    matricula.refresh_from_db()
    assert matricula.status == StatusMatricula.TRANCADA
