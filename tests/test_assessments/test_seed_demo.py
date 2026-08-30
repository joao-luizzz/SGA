import pytest
from django.core.management import call_command

from accounts.models import AuditoriaLog, CustomUser
from assessments.selectors import (
    SituacaoAcademica,
    calcular_resultado_academico,
)
from attendance.models import Falta
from enrollment.models import Matricula, StatusMatricula


@pytest.mark.django_db
def test_seed_demo_e_idempotente_e_cria_tres_cenarios():
    call_command('seed_demo')
    totais_iniciais = (
        CustomUser.objects.count(),
        Matricula.objects.count(),
        Falta.objects.count(),
        AuditoriaLog.objects.count(),
    )
    call_command('seed_demo')
    assert (
        CustomUser.objects.count(),
        Matricula.objects.count(),
        Falta.objects.count(),
        AuditoriaLog.objects.count(),
    ) == totais_iniciais

    situacoes = {}
    for chave in ('aprovado', 'exame', 'falta'):
        matricula = Matricula.objects.get(
            aluno__email=f'aluno.{chave}@sga.edu.br',
            status=StatusMatricula.ATIVA,
        )
        situacoes[chave] = calcular_resultado_academico(matricula)['situacao']

    assert situacoes == {
        'aprovado': SituacaoAcademica.APROVADO_DIRETO,
        'exame': SituacaoAcademica.ELEGIVEL_EXAME,
        'falta': SituacaoAcademica.REPROVADO_FALTA,
    }
