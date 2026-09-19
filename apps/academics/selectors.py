from django.db.models import Count, Prefetch, Q

from assessments.models import Nota, TipoAvaliacao
from assessments.selectors import calcular_resultado_academico
from attendance.models import Falta
from enrollment.models import Matricula, StatusMatricula

from .models import Curso, Turma


def get_relatorio_turmas(*, curso_id=None, periodo=None, turma_id=None):
    """Monta o relatório consolidado de turmas para a Coordenação."""
    matriculas_ativas = (
        Matricula.objects
        .filter(status=StatusMatricula.ATIVA)
        .select_related('aluno')
        .prefetch_related(Prefetch('notas', queryset=Nota.objects.order_by('tipo')))
        .order_by('aluno__full_name')
    )
    turmas = (
        Turma.objects
        .filter(ativo=True)
        .select_related('disciplina', 'disciplina__curso', 'professor')
        .prefetch_related(
            Prefetch(
                'matriculas',
                queryset=matriculas_ativas,
                to_attr='matriculas_relatorio',
            ),
            Prefetch(
                'faltas',
                queryset=Falta.objects.only('turma_id', 'aluno_id', 'presente'),
                to_attr='faltas_relatorio',
            ),
        )
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
        turma.linhas_relatorio = []
        for matricula in turma.matriculas_relatorio:
            notas = {nota.tipo: nota.valor for nota in matricula.notas.all()}
            resultado = calcular_resultado_academico(matricula, notas)
            linha = {
                'turma': turma,
                'matricula': matricula,
                'aluno': matricula.aluno,
                'identificador_matricula': matricula.pk,
                'p1': notas.get(TipoAvaliacao.P1),
                'p2': notas.get(TipoAvaliacao.P2),
                'trabalho': notas.get(TipoAvaliacao.TRABALHO),
                'exame': notas.get(TipoAvaliacao.EXAME),
                'resultado': resultado,
            }
            turma.linhas_relatorio.append(linha)
            linhas.append(linha)

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
