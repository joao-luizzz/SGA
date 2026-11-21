"""Views de pré-requisitos e aproveitamento de disciplinas (Fase 3)."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from accounts.decorators import role_required
from accounts.models import UserRole

from .forms import (
    AnaliseAproveitamentoForm, AproveitamentoForm, FiltroAproveitamentoForm, PreRequisitoForm,
)
from .models import Disciplina, PreRequisito, StatusAproveitamento
from .selectors import listar_aproveitamentos
from .services import (
    adicionar_pre_requisito, analisar_aproveitamento, registrar_aproveitamento,
    remover_pre_requisito,
)


def _adicionar_erros(form, erro):
    if hasattr(erro, 'message_dict'):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(campo if campo in form.fields else None, mensagem)
    else:
        for mensagem in erro.messages:
            form.add_error(None, mensagem)


@role_required(UserRole.COORDENACAO)
@require_http_methods(['GET', 'POST'])
def pre_requisitos_view(request, pk):
    disciplina = get_object_or_404(Disciplina.objects.select_related('curso'), pk=pk)
    form = PreRequisitoForm(request.POST or None, disciplina=disciplina)
    if request.method == 'POST' and form.is_valid():
        try:
            adicionar_pre_requisito(
                usuario=request.user, disciplina=disciplina,
                requisito=form.cleaned_data['requisito'],
            )
        except ValidationError as exc:
            _adicionar_erros(form, exc)
        else:
            messages.success(request, "Pré-requisito cadastrado.")
            return redirect('academics:pre_requisitos', pk=disciplina.pk)
    return render(request, 'academics/pre_requisitos.html', {
        'disciplina': disciplina,
        'form': form,
        'pre_requisitos': disciplina.pre_requisitos.select_related('requisito'),
        'dependentes': disciplina.requisito_de.select_related('disciplina'),
    })


@role_required(UserRole.COORDENACAO)
@require_POST
def pre_requisito_remover_view(request, pk):
    pre_requisito = get_object_or_404(PreRequisito, pk=pk)
    disciplina_id = pre_requisito.disciplina_id
    remover_pre_requisito(usuario=request.user, pre_requisito_id=pre_requisito.pk)
    messages.warning(request, "Pré-requisito removido.")
    return redirect('academics:pre_requisitos', pk=disciplina_id)


@role_required(UserRole.ALUNO, UserRole.SECRETARIA, UserRole.COORDENACAO)
@require_http_methods(['GET'])
def aproveitamento_index_view(request):
    filtros = FiltroAproveitamentoForm(request.GET)
    status = filtros.cleaned_data['status'] if filtros.is_valid() else ''
    registros = listar_aproveitamentos(request.user, status=status)
    return render(request, 'academics/aproveitamento_index.html', {
        'page_obj': Paginator(registros, 20).get_page(request.GET.get('page')),
        'filtros': filtros,
        'status': status,
        'pode_criar': request.user.is_superuser or request.user.role == UserRole.SECRETARIA,
    }, status=200 if filtros.is_valid() else 400)


@role_required(UserRole.SECRETARIA)
@require_http_methods(['GET', 'POST'])
def aproveitamento_criar_view(request):
    form = AproveitamentoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            registro = registrar_aproveitamento(usuario=request.user, **form.cleaned_data)
        except ValidationError as exc:
            _adicionar_erros(form, exc)
        else:
            messages.success(request, "Aproveitamento registrado como pendente de análise.")
            return redirect('academics:aproveitamento_detalhe', pk=registro.pk)
    return render(request, 'academics/aproveitamento_form.html', {'form': form})


@role_required(UserRole.ALUNO, UserRole.SECRETARIA, UserRole.COORDENACAO)
@require_http_methods(['GET'])
def aproveitamento_detalhe_view(request, pk):
    registro = get_object_or_404(listar_aproveitamentos(request.user), pk=pk)
    return _render_detalhe(request, registro, AnaliseAproveitamentoForm())


def _render_detalhe(request, registro, form, status=200):
    pode_analisar = registro.status == StatusAproveitamento.PENDENTE and (
        request.user.is_superuser or request.user.role == UserRole.COORDENACAO
    )
    return render(request, 'academics/aproveitamento_detalhe.html', {
        'registro': registro, 'form': form, 'pode_analisar': pode_analisar,
    }, status=status)


@role_required(UserRole.COORDENACAO)
@require_POST
def aproveitamento_analisar_view(request, pk):
    registro = get_object_or_404(listar_aproveitamentos(request.user), pk=pk)
    form = AnaliseAproveitamentoForm(request.POST)
    if form.is_valid():
        try:
            analisar_aproveitamento(
                usuario=request.user, aproveitamento_id=registro.pk,
                decisao=form.cleaned_data['decisao'],
                justificativa=form.cleaned_data['justificativa'],
            )
        except ValidationError as exc:
            _adicionar_erros(form, exc)
        else:
            messages.success(request, "Análise registrada.")
            return redirect('academics:aproveitamento_detalhe', pk=registro.pk)
    registro.refresh_from_db()
    return _render_detalhe(request, registro, form, status=400)
