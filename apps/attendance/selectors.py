from decimal import Decimal
from typing import Optional
from django.db.models import Count, Q
from .models import Falta


class SituacaoFrequencia:
    APROVADO = 'Aprovado'
    REPROVADO_FALTA = 'Reprovado por Falta'
    SEM_AULAS = 'Sem aulas registradas'


FREQUENCIA_MINIMA = Decimal('75.0')


def get_faltas_da_turma(turma, data_aula=None):
    """Retorna todos os registros de frequência de uma turma, opcionalmente filtrados por data."""
    qs = Falta.objects.filter(turma=turma).select_related('aluno')
    if data_aula:
        qs = qs.filter(data_aula=data_aula)
    return qs.order_by('data_aula', 'aluno__full_name')


def get_datas_de_aula_da_turma(turma):
    """Retorna lista de datas distintas em que houve chamada para uma turma."""
    return (
        Falta.objects
        .filter(turma=turma)
        .values_list('data_aula', flat=True)
        .distinct()
        .order_by('data_aula')
    )


def get_frequencia_do_aluno_na_turma(aluno, turma) -> dict:
    """
    Calcula a frequência percentual do aluno em uma turma (RN22).

    Returns:
        dict com keys: total_aulas, presencas, faltas, percentual, situacao
    """
    registros = Falta.objects.filter(turma=turma, aluno=aluno)
    total_aulas = registros.count()

    if total_aulas == 0:
        return {
            'total_aulas': 0,
            'presencas': 0,
            'faltas': 0,
            'percentual': Decimal('100.0'),
            'situacao': SituacaoFrequencia.SEM_AULAS,
        }

    presencas = registros.filter(presente=True).count()
    ausencias = total_aulas - presencas
    percentual = Decimal(str(round((presencas / total_aulas) * 100, 2)))

    situacao = (
        SituacaoFrequencia.APROVADO
        if percentual >= FREQUENCIA_MINIMA
        else SituacaoFrequencia.REPROVADO_FALTA
    )

    return {
        'total_aulas': total_aulas,
        'presencas': presencas,
        'faltas': ausencias,
        'percentual': percentual,
        'situacao': situacao,
    }


def get_boletim_frequencia_do_aluno(aluno):
    """
    Retorna o boletim de frequência do aluno em todas as turmas com matrícula ativa.
    Usado na view do aluno (RN03, RN22).
    """
    from enrollment.models import Matricula, StatusMatricula

    matriculas = (
        Matricula.objects
        .filter(aluno=aluno, status=StatusMatricula.ATIVA)
        .select_related('turma', 'turma__disciplina', 'turma__professor')
    )

    boletim = []
    for matricula in matriculas:
        freq = get_frequencia_do_aluno_na_turma(aluno, matricula.turma)
        boletim.append({
            'matricula': matricula,
            'turma': matricula.turma,
            **freq,
        })
    return boletim


def get_chamada_por_turma_e_data(turma, data_aula, alunos_matriculados):
    """
    Retorna mapa de presença para uma data específica numa turma.
    Usado para preencher formulário de chamada com estado atual.
    """
    registros_existentes = {
        f.aluno_id: f
        for f in Falta.objects.filter(turma=turma, data_aula=data_aula)
    }
    resultado = []
    for aluno in alunos_matriculados:
        registro = registros_existentes.get(aluno.pk)
        resultado.append({
            'aluno': aluno,
            'falta': registro,
            'presente': registro.presente if registro else None,
        })
    return resultado
