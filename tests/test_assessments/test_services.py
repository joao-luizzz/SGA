from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from accounts.models import AuditoriaLog, CustomUser, UserRole
from assessments.models import Nota, TipoAvaliacao
from assessments.services import lancar_notas_em_lote
from attendance.models import Falta
from enrollment.models import Matricula, StatusMatricula


NOTAS_PARCIAIS = {
    TipoAvaliacao.P1: Decimal('5.00'),
    TipoAvaliacao.P2: Decimal('5.00'),
    TipoAvaliacao.TRABALHO: Decimal('5.00'),
}


@pytest.mark.django_db
def test_cria_edita_e_audita_nota(
    matricula_assessments, turma_assessments, user_professor
):
    lancar_notas_em_lote(
        user_professor,
        turma_assessments,
        {matricula_assessments.pk: {TipoAvaliacao.P1: Decimal('7.00')}},
    )
    nota = Nota.objects.get()
    assert nota.valor == Decimal('7.00')
    assert AuditoriaLog.objects.filter(tabela_afetada='Nota', acao='CRIAR').count() == 1

    lancar_notas_em_lote(
        user_professor,
        turma_assessments,
        {matricula_assessments.pk: {TipoAvaliacao.P1: Decimal('8.00')}},
    )
    nota.refresh_from_db()
    assert nota.valor == Decimal('8.00')
    log = AuditoriaLog.objects.get(tabela_afetada='Nota', acao='EDITAR')
    assert '7.00' in log.valor_antigo
    assert '8.00' in log.valor_novo


@pytest.mark.django_db
def test_professor_de_turma_alheia_nao_lanca_notas(
    matricula_assessments, turma_assessments
):
    outro = CustomUser.objects.create_user(
        email='professor.alheio@sga.edu.br',
        full_name='Professor Alheio',
        role=UserRole.PROFESSOR,
        password='SenhaSegura123!',
    )
    with pytest.raises(ValidationError, match='professor responsável'):
        lancar_notas_em_lote(
            outro,
            turma_assessments,
            {matricula_assessments.pk: {TipoAvaliacao.P1: Decimal('7.00')}},
        )
    assert Nota.objects.count() == 0


@pytest.mark.django_db
def test_matricula_cancelada_nao_recebe_nota(
    matricula_assessments, turma_assessments, user_professor
):
    matricula_assessments.status = StatusMatricula.CANCELADA
    matricula_assessments.save(update_fields=['status'])
    with pytest.raises(ValidationError, match='matrículas ativas'):
        lancar_notas_em_lote(
            user_professor,
            turma_assessments,
            {matricula_assessments.pk: {TipoAvaliacao.P1: Decimal('7.00')}},
        )


@pytest.mark.django_db
def test_media_elegivel_permite_criar_e_editar_exame(
    matricula_assessments, turma_assessments, user_professor
):
    lancar_notas_em_lote(
        user_professor,
        turma_assessments,
        {matricula_assessments.pk: NOTAS_PARCIAIS},
    )
    lancar_notas_em_lote(
        user_professor,
        turma_assessments,
        {matricula_assessments.pk: {TipoAvaliacao.EXAME: Decimal('7.00')}},
    )
    lancar_notas_em_lote(
        user_professor,
        turma_assessments,
        {matricula_assessments.pk: {TipoAvaliacao.EXAME: Decimal('8.00')}},
    )
    assert Nota.objects.get(tipo=TipoAvaliacao.EXAME).valor == Decimal('8.00')


@pytest.mark.django_db
def test_frequencia_baixa_bloqueia_exame(
    matricula_assessments, turma_assessments, user_professor, user_aluno
):
    lancar_notas_em_lote(
        user_professor,
        turma_assessments,
        {matricula_assessments.pk: NOTAS_PARCIAIS},
    )
    for indice in range(4):
        Falta.objects.create(
            turma=turma_assessments,
            aluno=user_aluno,
            data_aula=date(2026, 8, 1) + timedelta(days=indice),
            presente=indice < 2,
            registrado_por=user_professor,
        )
    with pytest.raises(ValidationError, match='não está elegível'):
        lancar_notas_em_lote(
            user_professor,
            turma_assessments,
            {matricula_assessments.pk: {TipoAvaliacao.EXAME: Decimal('10.00')}},
        )
    assert not Nota.objects.filter(tipo=TipoAvaliacao.EXAME).exists()


@pytest.mark.django_db
def test_lote_reverte_todas_as_notas_quando_uma_falha(
    matricula_assessments, turma_assessments, user_professor
):
    outro_aluno = CustomUser.objects.create_user(
        email='outro.aluno.assessments@sga.edu.br',
        full_name='Outro Aluno',
        role=UserRole.ALUNO,
        password='SenhaSegura123!',
    )
    outra_matricula = Matricula.objects.create(
        aluno=outro_aluno,
        turma=turma_assessments,
        status=StatusMatricula.ATIVA,
    )
    with pytest.raises(ValidationError, match='não está elegível'):
        lancar_notas_em_lote(user_professor, turma_assessments, {
            matricula_assessments.pk: {TipoAvaliacao.P1: Decimal('9.00')},
            outra_matricula.pk: {TipoAvaliacao.EXAME: Decimal('10.00')},
        })
    assert Nota.objects.count() == 0
    assert AuditoriaLog.objects.count() == 0
