from .selectors import contar_nao_lidas


def notifications(request):
    """Apenas leitura: o contador não sincroniza comunicados a cada página."""
    return {'notificacoes_nao_lidas': contar_nao_lidas(getattr(request, 'user', None))}
