from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from accounts.decorators import role_required
from accounts.models import UserRole

from .forms import CancelamentoForm, CobrancaForm, FiltroCobrancaForm
from .models import StatusCobranca
from .selectors import listar_cobrancas, resumir_cobrancas
from .services import cancelar_cobranca, lancar_cobranca, registrar_pagamento


def _adicionar_erros(form, erro):
    if hasattr(erro, 'message_dict'):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(campo if campo in form.fields else None, mensagem)
    else:
        for mensagem in erro.messages:
            form.add_error(None, mensagem)


def _e_secretaria(usuario):
    return usuario.is_superuser or usuario.role == UserRole.SECRETARIA


@role_required(UserRole.ALUNO, UserRole.SECRETARIA)
@require_http_methods(['GET'])
def index(request):
    filtros = FiltroCobrancaForm(request.GET)
    status = filtros.cleaned_data['status'] if filtros.is_valid() else ''
    cobrancas = listar_cobrancas(request.user, status=status)
    return render(request, 'finance/index.html', {
        'page_obj': Paginator(cobrancas, 20).get_page(request.GET.get('page')),
        'resumo': resumir_cobrancas(listar_cobrancas(request.user)),
        'filtros': filtros, 'status': status,
        'e_secretaria': _e_secretaria(request.user),
    }, status=200 if filtros.is_valid() else 400)


@role_required(UserRole.SECRETARIA)
@require_http_methods(['GET', 'POST'])
def criar(request):
    form = CobrancaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            cobranca = lancar_cobranca(usuario=request.user, **form.cleaned_data)
        except ValidationError as exc:
            _adicionar_erros(form, exc)
        else:
            messages.success(request, "Cobrança lançada.")
            return redirect('finance:detalhe', pk=cobranca.pk)
    return render(request, 'finance/form.html', {'form': form})


def _render_detalhe(request, cobranca, form, status=200):
    return render(request, 'finance/detalhe.html', {
        'cobranca': cobranca, 'form': form,
        'pode_operar': _e_secretaria(request.user) and cobranca.status == StatusCobranca.ABERTA,
    }, status=status)


@role_required(UserRole.ALUNO, UserRole.SECRETARIA)
@require_http_methods(['GET'])
def detalhe(request, pk):
    cobranca = get_object_or_404(listar_cobrancas(request.user), pk=pk)
    return _render_detalhe(request, cobranca, CancelamentoForm())


@role_required(UserRole.SECRETARIA)
@require_POST
def pagar(request, pk):
    cobranca = get_object_or_404(listar_cobrancas(request.user), pk=pk)
    try:
        registrar_pagamento(usuario=request.user, cobranca_id=cobranca.pk)
    except ValidationError as exc:
        messages.error(request, ' '.join(exc.messages))
    else:
        messages.success(request, "Pagamento registrado.")
    return redirect('finance:detalhe', pk=cobranca.pk)


@role_required(UserRole.SECRETARIA)
@require_POST
def cancelar(request, pk):
    cobranca = get_object_or_404(listar_cobrancas(request.user), pk=pk)
    form = CancelamentoForm(request.POST)
    if form.is_valid():
        try:
            cancelar_cobranca(usuario=request.user, cobranca_id=cobranca.pk,
                              justificativa=form.cleaned_data['justificativa'])
        except ValidationError as exc:
            _adicionar_erros(form, exc)
        else:
            messages.warning(request, "Cobrança cancelada.")
            return redirect('finance:detalhe', pk=cobranca.pk)
    cobranca.refresh_from_db()
    return _render_detalhe(request, cobranca, form, status=400)
