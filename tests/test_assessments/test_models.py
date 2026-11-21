from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from assessments.models import Nota, TipoAvaliacao


@pytest.mark.django_db
def test_nota_aceita_limites(matricula_assessments, user_professor):
    for tipo, valor in ((TipoAvaliacao.P1, '0.00'), (TipoAvaliacao.P2, '10.00')):
        nota = Nota(
            matricula=matricula_assessments,
            tipo=tipo,
            valor=Decimal(valor),
            registrado_por=user_professor,
        )
        nota.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize('valor', ['-0.01', '10.01'])
def test_nota_rejeita_valor_fora_da_escala(
    matricula_assessments, user_professor, valor
):
    nota = Nota(
        matricula=matricula_assessments,
        tipo=TipoAvaliacao.P1,
        valor=Decimal(valor),
        registrado_por=user_professor,
    )
    with pytest.raises(ValidationError):
        nota.full_clean()


@pytest.mark.django_db
def test_uma_nota_por_matricula_e_tipo(matricula_assessments, user_professor):
    Nota.objects.create(
        matricula=matricula_assessments,
        tipo=TipoAvaliacao.P1,
        valor=Decimal('7.00'),
        registrado_por=user_professor,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        Nota.objects.create(
            matricula=matricula_assessments,
            tipo=TipoAvaliacao.P1,
            valor=Decimal('8.00'),
            registrado_por=user_professor,
        )
