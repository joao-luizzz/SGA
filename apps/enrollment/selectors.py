from django.db.models import Count, Q
from .models import Matricula, StatusMatricula


def get_matriculas_ativas_da_turma(turma):
    """Retorna queryset de matrículas ativas de uma turma."""
    return Matricula.objects.filter(turma=turma, status=StatusMatricula.ATIVA).select_related('aluno')


def get_matriculas_do_aluno(aluno):
    """Retorna queryset de matrículas de um aluno, ordenadas por turma."""
    return (
        Matricula.objects
        .filter(aluno=aluno)
        .select_related('turma', 'turma__disciplina', 'turma__professor')
        .order_by('-turma__periodo_letivo', 'turma__disciplina__nome')
    )


def get_matriculas_administrativas():
    """Retorna as matrículas para a gestão administrativa da Secretaria."""
    return (
        Matricula.objects
        .select_related('aluno', 'turma', 'turma__disciplina')
        .order_by('-matriculado_em')
    )


def contar_vagas_ocupadas(turma):
    """Conta o número de matrículas ativas em uma turma (RN11)."""
    return Matricula.objects.filter(turma=turma, status=StatusMatricula.ATIVA).count()


def turma_pode_receber_matricula(turma):
    """Verifica se a turma ainda tem vagas e está disponível para matrícula (RN10, RN40)."""
    if not turma.pode_receber_matricula():
        return False
    return contar_vagas_ocupadas(turma) < turma.vagas_maximas


def aluno_ja_matriculado(aluno, turma):
    """Verifica se o aluno já possui matrícula ativa nesta turma (RN10 — sem duplicidade)."""
    return Matricula.objects.filter(
        aluno=aluno,
        turma=turma,
        status=StatusMatricula.ATIVA,
    ).exists()


def get_pre_requisitos_pendentes(aluno, disciplina):
    """Disciplinas exigidas por `disciplina` que o aluno ainda não cumpriu (RN19).

    Cumpre o pré-requisito um aproveitamento deferido ou uma matrícula não
    cancelada com resultado calculado de aprovação (direta ou após exame).
    """
    from academics.models import Aproveitamento, Disciplina, StatusAproveitamento
    from assessments.selectors import SituacaoAcademica, calcular_resultado_academico

    aprovadas = {SituacaoAcademica.APROVADO_DIRETO, SituacaoAcademica.APROVADO_EXAME}
    requisitos = Disciplina.objects.filter(requisito_de__disciplina=disciplina).order_by('nome')
    aproveitadas = set(
        Aproveitamento.objects.filter(
            aluno=aluno, disciplina__in=requisitos, status=StatusAproveitamento.DEFERIDO,
        ).values_list('disciplina_id', flat=True)
    )

    pendentes = []
    for requisito in requisitos:
        if requisito.pk in aproveitadas:
            continue
        matriculas = (
            Matricula.objects.filter(aluno=aluno, turma__disciplina=requisito)
            .exclude(status=StatusMatricula.CANCELADA)
            .select_related('aluno', 'turma')
        )
        if not any(calcular_resultado_academico(m)['situacao'] in aprovadas for m in matriculas):
            pendentes.append(requisito)
    return pendentes
