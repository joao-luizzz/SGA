from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import role_required
from accounts.models import UserRole

from .forms import EmissaoForm, VerificacaoForm
from .selectors import listar_documentos
from .services import emitir_documento, verificar_documento


def _e_secretaria(usuario):
    return usuario.is_superuser or usuario.role == UserRole.SECRETARIA


@role_required(UserRole.ALUNO, UserRole.SECRETARIA)
@require_GET
def index(request):
    return render(request, 'documents/index.html', {
        'page_obj': Paginator(listar_documentos(request.user), 20).get_page(request.GET.get('page')),
        'form': EmissaoForm(),
        'e_secretaria': _e_secretaria(request.user),
    })


@role_required(UserRole.ALUNO, UserRole.SECRETARIA)
@require_POST
def emitir(request):
    form = EmissaoForm(request.POST)
    if form.is_valid():
        aluno = form.cleaned_data['aluno'] if _e_secretaria(request.user) else request.user
        if aluno is None:
            messages.error(request, "Selecione o aluno.")
            return redirect('documents:index')
        try:
            documento = emitir_documento(usuario=request.user, aluno=aluno, tipo=form.cleaned_data['tipo'])
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
            return redirect('documents:index')
        messages.success(request, "Documento emitido.")
        return redirect('documents:detalhe', pk=documento.pk)
    messages.error(request, "Não foi possível emitir: confira os dados informados.")
    return redirect('documents:index')


@role_required(UserRole.ALUNO, UserRole.SECRETARIA)
@require_GET
def detalhe(request, pk):
    documento = get_object_or_404(listar_documentos(request.user), pk=pk)
    url_verificacao = request.build_absolute_uri(reverse('documents:verificar'))
    return render(request, 'documents/detalhe.html', {
        'documento': documento,
        'conteudo': documento.conteudo,
        'url_verificacao': url_verificacao,
    })


@require_GET
def verificar(request):
    """Página pública, sem login (RN23)."""
    form = VerificacaoForm(request.GET or None)
    resultado, consultado = None, False
    if form.is_valid():
        consultado = True
        resultado = verificar_documento(
            codigo=form.cleaned_data['codigo'], ip=request.META.get('REMOTE_ADDR', ''),
        )
    response = render(request, 'documents/verificar.html', {
        'form': form, 'resultado': resultado, 'consultado': consultado,
    })
    response['Referrer-Policy'] = 'no-referrer'
    return response
