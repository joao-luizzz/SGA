from datetime import date, timedelta
from decimal import Decimal

import pytest

from assessments.models import Nota, TipoAvaliacao
from assessments.selectors import SituacaoAcademica, calcular_resultado_academico
from attendance.models import Falta


def criar_notas(matricula, professor, valores):
    for tipo, valor in valores.items():
        Nota.objects.create(
            matricula=matricula,
            tipo=tipo,
            valor=Decimal(valor),
            registrado_por=professor,
        )


@pytest.mark.django_db
def test_notas_incompletas_ficam_em_andamento(matricula_assessments, user_professor):
    criar_notas(matricula_assessments, user_professor, {TipoAvaliacao.P1: '8.00'})
    resultado = calcular_resultado_academico(matricula_assessments)
    assert resultado['situacao'] == SituacaoAcademica.EM_ANDAMENTO
    assert resultado['media_parcial'] is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('valores', 'situacao', 'media'),
    [
        (('6.00', '6.00', '6.00'), SituacaoAcademica.APROVADO_DIRETO, Decimal('6.00')),
        (('4.00', '4.00', '4.00'), SituacaoAcademica.ELEGIVEL_EXAME, Decimal('4.00')),
        (('3.99', '3.99', '3.99'), SituacaoAcademica.REPROVADO_NOTA, Decimal('3.99')),
    ],
)
def test_limites_da_media_parcial(
    matricula_assessments, user_professor, valores, situacao, media
):
    criar_notas(matricula_assessments, user_professor, dict(zip(
        (TipoAvaliacao.P1, TipoAvaliacao.P2, TipoAvaliacao.TRABALHO),
        valores,
    )))
    resultado = calcular_resultado_academico(matricula_assessments)
    assert resultado['media_parcial'] == media
    assert resultado['situacao'] == situacao


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('exame', 'situacao'),
    [
        ('7.00', SituacaoAcademica.APROVADO_EXAME),
        ('6.98', SituacaoAcademica.REPROVADO_NOTA),
    ],
)
def test_media_final(matricula_assessments, user_professor, exame, situacao):
    criar_notas(matricula_assessments, user_professor, {
        TipoAvaliacao.P1: '5.00',
        TipoAvaliacao.P2: '5.00',
        TipoAvaliacao.TRABALHO: '5.00',
        TipoAvaliacao.EXAME: exame,
    })
    resultado = calcular_resultado_academico(matricula_assessments)
    assert resultado['situacao'] == situacao
    media_esperada = Decimal('6.00') if exame == '7.00' else Decimal('5.99')
    assert resultado['media_final'] == media_esperada


@pytest.mark.django_db
def test_frequencia_baixa_prevalece_sobre_notas(
    matricula_assessments, user_professor, user_aluno, turma_assessments
):
    criar_notas(matricula_assessments, user_professor, {
        TipoAvaliacao.P1: '10.00',
        TipoAvaliacao.P2: '10.00',
        TipoAvaliacao.TRABALHO: '10.00',
    })
    for indice in range(4):
        Falta.objects.create(
            turma=turma_assessments,
            aluno=user_aluno,
            data_aula=date(2026, 8, 1) + timedelta(days=indice),
            presente=indice < 2,
            registrado_por=user_professor,
        )
    resultado = calcular_resultado_academico(matricula_assessments)
    assert resultado['frequencia']['percentual'] == Decimal('50.0')
    assert resultado['media_parcial'] == Decimal('10.00')
    assert resultado['situacao'] == SituacaoAcademica.REPROVADO_FALTA
