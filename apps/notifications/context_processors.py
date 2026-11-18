from .selectors import contar_nao_lidas
from .services import sincronizar_comunicados


def notifications(request):
    usuario = getattr(request, 'user', None)
    sincronizar_comunicados(usuario)
    return {'notificacoes_nao_lidas': contar_nao_lidas(usuario)}
