from io import StringIO

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


@pytest.mark.django_db
def test_seed_demo_prepara_cenarios_da_fase_3():
    from django.core.exceptions import ValidationError

    from academics.models import Aproveitamento, PreRequisito, StatusAproveitamento, Turma
    from enrollment.services import matricular_aluno_administrativo
    from finance.models import Cobranca

    call_command('seed_demo', stdout=StringIO())
    call_command('seed_demo', stdout=StringIO())

    requisito = PreRequisito.objects.select_related('disciplina', 'requisito').get()
    assert (requisito.disciplina.codigo, requisito.requisito.codigo) == ('BD-DEMO', 'ES-DEMO')
    assert Aproveitamento.objects.get().status == StatusAproveitamento.PENDENTE
    cobrancas = list(Cobranca.objects.order_by('vencimento'))
    assert len(cobrancas) == 2
    assert cobrancas[0].em_atraso and not cobrancas[1].em_atraso

    secretaria = CustomUser.objects.get(email='secretaria.demo@sga.edu.br')
    turma = Turma.objects.get(disciplina__codigo='BD-DEMO')
    aprovado = CustomUser.objects.get(email='aluno.aprovado@sga.edu.br')
    faltoso = CustomUser.objects.get(email='aluno.falta@sga.edu.br')
    assert matricular_aluno_administrativo(secretaria, aprovado, turma)
    with pytest.raises(ValidationError, match='pré-requisitos'):
        matricular_aluno_administrativo(secretaria, faltoso, turma)
