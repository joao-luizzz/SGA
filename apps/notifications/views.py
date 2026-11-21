from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .selectors import listar_notificacoes
from .services import marcar_como_lida, marcar_todas_como_lidas, sincronizar_comunicados


@login_required
def central(request):
    sincronizar_comunicados(request.user)
    pagina = Paginator(listar_notificacoes(request.user), 20).get_page(request.GET.get('page'))
    return render(request, 'notifications/central.html', {'page_obj': pagina})


@login_required
def detalhe(request, pk):
    notificacao = get_object_or_404(listar_notificacoes(request.user), pk=pk)
    return render(request, 'notifications/detalhe.html', {'notificacao': notificacao})


@login_required
@require_POST
def ler(request, pk):
    marcar_como_lida(request.user, pk)
    return redirect('notifications:detalhe', pk=pk)


@login_required
@require_POST
def ler_todas(request):
    marcar_todas_como_lidas(request.user)
    return redirect('notifications:central')
