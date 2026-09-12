from django.db.models import Q, QuerySet
from django.utils import timezone
from academics.models import Turma
from enrollment.models import Matricula, StatusMatricula
from .models import Comunicado, EscopoComunicado


def listar_comunicados_para_usuario(usuario) -> QuerySet[Comunicado]:
    """
    Retorna os comunicados vigentes direcionados ao perfil/vínculos do usuário autenticado.
    """
    if not usuario or not usuario.is_authenticated:
        return Comunicado.objects.none()

    agora = timezone.now()
    qs_base = Comunicado.objects.filter(
        ativo=True,
        publicar_em__lte=agora
    ).filter(
        Q(expirar_em__isnull=True) | Q(expirar_em__gte=agora)
    ).select_related('autor', 'curso', 'turma', 'turma__disciplina')

    # Coordenação, Secretaria e Superusuário veem todos os comunicados vigentes no mural
    if usuario.is_superuser or usuario.role in ('COORDENACAO', 'SECRETARIA'):
        return qs_base.order_by('-publicar_em')

    # Filtro para Alunos
    if usuario.role == 'ALUNO':
        turmas_ids = Matricula.objects.filter(
            aluno=usuario,
            status=StatusMatricula.ATIVA
        ).values_list('turma_id', flat=True)

        cursos_ids = Turma.objects.filter(
            id__in=turmas_ids
        ).values_list('disciplina__curso_id', flat=True).distinct()

        filtro = (
            Q(escopo=EscopoComunicado.GERAL) |
            Q(escopo=EscopoComunicado.PAPEL, papel_destino='ALUNO') |
            Q(escopo=EscopoComunicado.TURMA, turma_id__in=turmas_ids) |
            Q(escopo=EscopoComunicado.CURSO, curso_id__in=cursos_ids)
        )
        return qs_base.filter(filtro).order_by('-publicar_em')

    # Filtro para Professores
    if usuario.role == 'PROFESSOR':
        turmas_ids = Turma.objects.filter(
            professor=usuario,
            ativo=True
        ).values_list('id', flat=True)

        cursos_ids = Turma.objects.filter(
            id__in=turmas_ids
        ).values_list('disciplina__curso_id', flat=True).distinct()

        filtro = (
            Q(escopo=EscopoComunicado.GERAL) |
            Q(escopo=EscopoComunicado.PAPEL, papel_destino='PROFESSOR') |
            Q(escopo=EscopoComunicado.TURMA, turma_id__in=turmas_ids) |
            Q(escopo=EscopoComunicado.CURSO, curso_id__in=cursos_ids)
        )
        return qs_base.filter(filtro).order_by('-publicar_em')

    return qs_base.filter(escopo=EscopoComunicado.GERAL).order_by('-publicar_em')


def listar_comunicados_gerenciamento(usuario) -> QuerySet[Comunicado]:
    """
    Retorna todos os comunicados para painel administrativo/gerencial.
    """
    if not usuario or not usuario.is_authenticated:
        return Comunicado.objects.none()

    if usuario.is_superuser or usuario.role in ('COORDENACAO', 'SECRETARIA'):
        return Comunicado.objects.all().select_related('autor', 'curso', 'turma', 'turma__disciplina').order_by('-criado_em')

    return Comunicado.objects.none()
