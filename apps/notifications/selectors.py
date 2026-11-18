from django.db.models import Q
from communications.selectors import listar_comunicados_para_usuario
from .models import Notificacao


def listar_notificacoes(usuario):
    """Inclusive superusuários consultam somente a própria central pessoal."""
    if not usuario or not usuario.is_authenticated or not usuario.is_active:
        return Notificacao.objects.none()
    comunicados = listar_comunicados_para_usuario(usuario).order_by().values('pk')
    return Notificacao.objects.filter(destinatario=usuario).filter(
        Q(comunicado__isnull=True) | Q(comunicado_id__in=comunicados),
    ).select_related('comunicado')


def contar_nao_lidas(usuario):
    return listar_notificacoes(usuario).filter(lida_em__isnull=True).count()
