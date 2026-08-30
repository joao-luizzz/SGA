from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from accounts.models import AuditoriaLog, CustomUser, UserRole
from academics.models import Curso, Disciplina, Turma
from assessments.models import Nota, TipoAvaliacao
from assessments.selectors import SituacaoAcademica, calcular_resultado_academico
from assessments.services import lancar_notas_em_lote
from attendance.models import Falta
from attendance.services import registrar_chamada
from enrollment.services import matricular_aluno_administrativo


@pytest.fixture
def turma_integracao(db, user_professor):
    curso = Curso.objects.create(nome='Curso Integração', codigo='INT')
    disciplina = Disciplina.objects.create(
        nome='Disciplina Integração', codigo='INT-01', carga_horaria=40, curso=curso
    )
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/2',
        horarios='SEX 08:00-10:00',
        sala='Sala INT',
        vagas_maximas=10,
        professor=user_professor,
        ativo=True,
    )


@pytest.mark.django_db
def test_fluxo_completo_matricula_chamada_notas_media_e_situacao(
    user_secretaria, user_professor, user_aluno, turma_integracao
):
    matricula = matricular_aluno_administrativo(
        user_secretaria, user_aluno, turma_integracao
    )
    for indice in range(4):
        registrar_chamada(
            user_professor,
            turma_integracao,
            date(2026, 8, 7) + timedelta(days=indice * 7),
            {user_aluno.pk: True},
        )
    lancar_notas_em_lote(user_professor, turma_integracao, {
        matricula.pk: {
            TipoAvaliacao.P1: Decimal('7.00'),
            TipoAvaliacao.P2: Decimal('6.00'),
            TipoAvaliacao.TRABALHO: Decimal('8.00'),
        }
    })

    resultado = calcular_resultado_academico(matricula)
    assert resultado['media_parcial'] == Decimal('7.00')
    assert resultado['frequencia']['percentual'] == Decimal('100.0')
    assert resultado['situacao'] == SituacaoAcademica.APROVADO_DIRETO
    assert Nota.objects.filter(matricula=matricula).count() == 3
    assert Falta.objects.filter(aluno=user_aluno, turma=turma_integracao).count() == 4
    assert AuditoriaLog.objects.filter(tabela_afetada='Nota').count() == 3
    assert AuditoriaLog.objects.filter(tabela_afetada='Falta').count() == 4


@pytest.mark.django_db
def test_faixa_de_exame_permite_e_frequencia_baixa_bloqueia(
    user_secretaria, user_professor, user_aluno, turma_integracao
):
    elegivel = matricular_aluno_administrativo(
        user_secretaria, user_aluno, turma_integracao
    )
    reprovado = CustomUser.objects.create_user(
        email='reprovado.integracao@sga.edu.br',
        full_name='Reprovado Integração',
        role=UserRole.ALUNO,
        password='SenhaSegura123!',
    )
    matricula_reprovado = matricular_aluno_administrativo(
        user_secretaria, reprovado, turma_integracao
    )
    notas_parciais = {
        TipoAvaliacao.P1: Decimal('5.00'),
        TipoAvaliacao.P2: Decimal('5.00'),
        TipoAvaliacao.TRABALHO: Decimal('5.00'),
    }
    lancar_notas_em_lote(user_professor, turma_integracao, {
        elegivel.pk: notas_parciais,
        matricula_reprovado.pk: notas_parciais,
    })
    for indice in range(4):
        registrar_chamada(
            user_professor,
            turma_integracao,
            date(2026, 9, 4) + timedelta(days=indice * 7),
            {user_aluno.pk: True, reprovado.pk: indice < 2},
        )

    lancar_notas_em_lote(user_professor, turma_integracao, {
        elegivel.pk: {TipoAvaliacao.EXAME: Decimal('7.00')}
    })
    assert calcular_resultado_academico(elegivel)['situacao'] == SituacaoAcademica.APROVADO_EXAME

    with pytest.raises(ValidationError, match='não está elegível'):
        lancar_notas_em_lote(user_professor, turma_integracao, {
            matricula_reprovado.pk: {TipoAvaliacao.EXAME: Decimal('10.00')}
        })
    assert calcular_resultado_academico(matricula_reprovado)['situacao'] == SituacaoAcademica.REPROVADO_FALTA


@pytest.mark.django_db
def test_professor_alheio_nao_lanca_nota_nem_frequencia(
    user_secretaria, user_aluno, turma_integracao
):
    matricula = matricular_aluno_administrativo(
        user_secretaria, user_aluno, turma_integracao
    )
    professor_alheio = CustomUser.objects.create_user(
        email='alheio.integracao@sga.edu.br',
        full_name='Professor Alheio Integração',
        role=UserRole.PROFESSOR,
        password='SenhaSegura123!',
    )
    with pytest.raises(ValidationError, match='professor responsável'):
        lancar_notas_em_lote(professor_alheio, turma_integracao, {
            matricula.pk: {TipoAvaliacao.P1: Decimal('10.00')}
        })
    with pytest.raises(ValidationError, match='professor responsável'):
        registrar_chamada(
            professor_alheio, turma_integracao, date(2026, 8, 7),
            {user_aluno.pk: True},
        )
    assert Nota.objects.count() == 0
    assert Falta.objects.count() == 0
    assert AuditoriaLog.objects.count() == 0
