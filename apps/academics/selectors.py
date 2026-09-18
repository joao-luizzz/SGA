from django.db.models import Count, Q
from assessments.selectors import calcular_resultado_academico, get_matriculas_com_notas_da_turma
from enrollment.models import StatusMatricula

from .models import Curso, Turma


def get_relatorio_turmas(*, curso_id=None, periodo=None, turma_id=None):
    """Monta o relatório consolidado de turmas para a Coordenação."""
    turmas = (
        Turma.objects
        .filter(ativo=True)
        .select_related('disciplina', 'disciplina__curso', 'professor')
        .annotate(
            matriculas_ativas=Count(
                'matriculas',
                filter=Q(matriculas__status=StatusMatricula.ATIVA),
            )
        )
        .order_by('-periodo_letivo', 'disciplina__nome')
    )

    if curso_id:
        turmas = turmas.filter(disciplina__curso_id=curso_id)
    if periodo:
        turmas = turmas.filter(periodo_letivo=periodo)
    if turma_id:
        turmas = turmas.filter(pk=turma_id)

    turmas = list(turmas)
    linhas = []
    for turma in turmas:
        for matricula in get_matriculas_com_notas_da_turma(turma):
            resultado = calcular_resultado_academico(matricula)
            linhas.append({
                'turma': turma,
                'matricula': matricula,
                'aluno': matricula.aluno,
                'resultado': resultado,
            })

    return {
        'turmas': turmas,
        'linhas': linhas,
        'cursos': Curso.objects.filter(ativo=True).order_by('nome'),
        'periodos': (
            Turma.objects
            .filter(ativo=True)
            .values_list('periodo_letivo', flat=True)
            .distinct()
            .order_by('-periodo_letivo')
        ),
        'filtros': {
            'curso': str(curso_id or ''),
            'periodo': periodo or '',
            'turma': str(turma_id or ''),
        },
    }