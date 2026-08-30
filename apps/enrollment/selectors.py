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
