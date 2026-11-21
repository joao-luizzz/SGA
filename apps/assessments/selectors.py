from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Prefetch

from attendance.selectors import get_frequencia_do_aluno_na_turma
from enrollment.models import Matricula, StatusMatricula

from .models import Nota, TipoAvaliacao


DUAS_CASAS = Decimal('0.01')
FREQUENCIA_MINIMA = Decimal('75.00')


class SituacaoAcademica:
    EM_ANDAMENTO = 'Em andamento'
    APROVADO_DIRETO = 'Aprovado Direto'
    ELEGIVEL_EXAME = 'Elegível para Exame Final'
    APROVADO_EXAME = 'Aprovado após Exame'
    REPROVADO_NOTA = 'Reprovado por Nota'
    REPROVADO_FALTA = 'Reprovado por Falta'


def _arredondar(valor):
    return valor.quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)


def get_notas_da_matricula(matricula):
    return {nota.tipo: nota.valor for nota in matricula.notas.all()}


def calcular_resultado_academico(matricula, notas=None):
    """Calcula médias e situação sem persistir dados derivados."""
    notas = notas if notas is not None else get_notas_da_matricula(matricula)
    frequencia = get_frequencia_do_aluno_na_turma(
        matricula.aluno,
        matricula.turma,
    )

    tipos_parciais = (TipoAvaliacao.P1, TipoAvaliacao.P2, TipoAvaliacao.TRABALHO)
    if any(tipo not in notas for tipo in tipos_parciais):
        return {
            'media_parcial': None,
            'media_final': None,
            'media_parcial_exata': None,
            'media_final_exata': None,
            'situacao': SituacaoAcademica.EM_ANDAMENTO,
            'frequencia': frequencia,
        }

    # As comparações usam a média exata (regra do AGENTS.md: MP >= 6, 4 <= MP < 6,
    # MF >= 6); o arredondamento para duas casas é apenas para exibição. Assim,
    # MP 5,9967 aparece como "6,00", mas o aluno vai a exame.
    mp_exata = sum(notas[tipo] for tipo in tipos_parciais) / Decimal('3')
    mf_exata = None
    if frequencia['total_aulas'] and frequencia['percentual'] < FREQUENCIA_MINIMA:
        situacao = SituacaoAcademica.REPROVADO_FALTA
    elif mp_exata >= Decimal('6'):
        situacao = SituacaoAcademica.APROVADO_DIRETO
    elif mp_exata < Decimal('4'):
        situacao = SituacaoAcademica.REPROVADO_NOTA
    elif TipoAvaliacao.EXAME not in notas:
        situacao = SituacaoAcademica.ELEGIVEL_EXAME
    else:
        mf_exata = (mp_exata + notas[TipoAvaliacao.EXAME]) / Decimal('2')
        situacao = (
            SituacaoAcademica.APROVADO_EXAME
            if mf_exata >= Decimal('6')
            else SituacaoAcademica.REPROVADO_NOTA
        )

    return {
        'media_parcial': _arredondar(mp_exata),
        'media_final': _arredondar(mf_exata) if mf_exata is not None else None,
        'media_parcial_exata': mp_exata,
        'media_final_exata': mf_exata,
        'situacao': situacao,
        'frequencia': frequencia,
    }


def pode_realizar_exame(matricula):
    """Valida a faixa de média e a frequência, independentemente de exame já lançado."""
    notas = get_notas_da_matricula(matricula)
    notas_sem_exame = {
        tipo: valor for tipo, valor in notas.items() if tipo != TipoAvaliacao.EXAME
    }
    resultado = calcular_resultado_academico(matricula, notas_sem_exame)
    return resultado['situacao'] == SituacaoAcademica.ELEGIVEL_EXAME


def get_turmas_do_professor(professor):
    return (
        professor.turmas_ministradas
        .filter(ativo=True)
        .select_related('disciplina')
        .order_by('-periodo_letivo', 'disciplina__nome')
    )


def get_matriculas_com_notas_da_turma(turma):
    return (
        Matricula.objects
        .filter(turma=turma, status=StatusMatricula.ATIVA)
        .select_related('aluno', 'turma', 'turma__disciplina')
        .prefetch_related(Prefetch('notas', queryset=Nota.objects.order_by('tipo')))
        .order_by('aluno__full_name')
    )


def get_boletim_do_aluno(aluno):
    matriculas = (
        Matricula.objects
        .filter(aluno=aluno, status=StatusMatricula.ATIVA)
        .select_related('aluno', 'turma', 'turma__disciplina', 'turma__professor')
        .prefetch_related(Prefetch('notas', queryset=Nota.objects.order_by('tipo')))
        .order_by('-turma__periodo_letivo', 'turma__disciplina__nome')
    )
    boletim = []
    for matricula in matriculas:
        notas = get_notas_da_matricula(matricula)
        boletim.append({
            'matricula': matricula,
            'notas': notas,
            'p1': notas.get(TipoAvaliacao.P1),
            'p2': notas.get(TipoAvaliacao.P2),
            'trabalho': notas.get(TipoAvaliacao.TRABALHO),
            'exame': notas.get(TipoAvaliacao.EXAME),
            **calcular_resultado_academico(matricula, notas),
        })
    return boletim
