from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from academics.models import Turma
from enrollment.models import Matricula, StatusMatricula
from .models import MaterialAcademico


def get_turmas_para_materiais(usuario) -> QuerySet[Turma]:
    """
    Retorna as turmas relevantes para o usuário visualizar materiais.
    """
    if not usuario or not usuario.is_authenticated:
        return Turma.objects.none()

    if usuario.role == 'ALUNO':
        turmas_ids = Matricula.objects.filter(
            aluno=usuario,
            status=StatusMatricula.ATIVA
        ).values_list('turma_id', flat=True)
        return Turma.objects.filter(id__in=turmas_ids, ativo=True).select_related('disciplina', 'professor')

    if usuario.role == 'PROFESSOR':
        return Turma.objects.filter(professor=usuario, ativo=True).select_related('disciplina', 'professor')

    if usuario.role in ('COORDENACAO', 'SECRETARIA') or usuario.is_superuser:
        return Turma.objects.filter(ativo=True).select_related('disciplina', 'professor')

    return Turma.objects.none()


def usuario_pode_acessar_turma(turma: Turma, usuario) -> bool:
    """
    Verifica se o usuário tem permissão para visualizar materiais da turma.
    """
    if not usuario or not usuario.is_authenticated:
        return False

    if usuario.role in ('COORDENACAO', 'SECRETARIA') or usuario.is_superuser:
        return True

    if usuario.role == 'PROFESSOR':
        return turma.professor_id == usuario.id

    if usuario.role == 'ALUNO':
        return Matricula.objects.filter(
            aluno=usuario,
            turma=turma,
            status=StatusMatricula.ATIVA
        ).exists()

    return False


def listar_materiais_turma(turma: Turma, usuario) -> QuerySet[MaterialAcademico]:
    """
    Lista os materiais de uma turma se o usuário tiver acesso.
    """
    if not usuario_pode_acessar_turma(turma, usuario):
        raise PermissionDenied("Você não tem acesso aos materiais desta turma.")

    return MaterialAcademico.objects.filter(turma=turma).select_related('turma', 'autor')
