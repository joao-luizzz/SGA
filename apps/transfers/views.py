from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.decorators import role_required
from accounts.models import UserRole
from .forms import AnaliseTransferenciaForm, FiltroTransferenciaForm, SolicitacaoTransferenciaForm
from .models import StatusTransferencia
from .permissions import PAPEIS_CONSULTA, exigir_perfil
from .selectors import listar_transferencias
from .services import analisar_transferencia, solicitar_transferencia


def _adicionar_erros(form, erro):
    if hasattr(erro, 'message_dict'):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(campo if campo in form.fields else None, mensagem)
    else:
        for mensagem in erro.messages:
            form.add_error(None, mensagem)


@role_required(*PAPEIS_CONSULTA)
@require_http_methods(['GET'])
def index(request):
    registros = listar_transferencias(usuario=request.user)
    filtros = FiltroTransferenciaForm(request.GET)
    if filtros.is_valid():
        registros = listar_transferencias(
            usuario=request.user, status=filtros.cleaned_data['status'],
            tipo=filtros.cleaned_data['tipo'], curso_id=filtros.cleaned_data['curso'],
        )
    else:
        registros = registros.none()
    parametros = request.GET.copy()
    parametros.pop('page', None)
    return render(request, 'transfers/index.html', {
        'page_obj': Paginator(registros, 20).get_page(request.GET.get('page')),
        'filtros': filtros, 'parametros': parametros.urlencode(),
        'pode_criar': request.user.is_superuser or request.user.role == UserRole.SECRETARIA,
    }, status=200 if filtros.is_valid() else 400)


@role_required(UserRole.SECRETARIA)
@require_http_methods(['GET', 'POST'])
def criar(request):
    exigir_perfil(request.user, UserRole.SECRETARIA)
    form = SolicitacaoTransferenciaForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            registro = solicitar_transferencia(usuario=request.user, **form.cleaned_data)
        except ValidationError as exc:
            _adicionar_erros(form, exc)
        else:
            messages.success(request, 'Solicitação registrada como pendente. Nenhuma matrícula foi alterada.')
            return redirect('transfers:detalhe', pk=registro.pk)
    return render(request, 'transfers/form.html', {'form': form})


@role_required(*PAPEIS_CONSULTA)
@require_http_methods(['GET'])
def detalhe(request, pk):
    registro = get_object_or_404(listar_transferencias(usuario=request.user), pk=pk)
    return render(request, 'transfers/detalhe.html', {
        'registro': registro,
        'pode_analisar': registro.status == StatusTransferencia.PENDENTE and (
            request.user.is_superuser or request.user.role == UserRole.COORDENACAO
        ),
        'form': AnaliseTransferenciaForm(),
    })


@role_required(UserRole.COORDENACAO)
@require_http_methods(['POST'])
def analisar(request, pk):
    registro = get_object_or_404(listar_transferencias(usuario=request.user), pk=pk)
    form = AnaliseTransferenciaForm(request.POST)
    if form.is_valid():
        try:
            analisar_transferencia(usuario=request.user, solicitacao_id=registro.pk, **form.cleaned_data)
        except ValidationError as exc:
            _adicionar_erros(form, exc)
            registro.refresh_from_db()
        else:
            messages.success(request, 'Decisão registrada. O histórico acadêmico e as matrículas foram preservados.')
            return redirect('transfers:detalhe', pk=registro.pk)
    return render(request, 'transfers/detalhe.html', {
        'registro': registro, 'form': form,
        'pode_analisar': registro.status == StatusTransferencia.PENDENTE,
    }, status=400)
