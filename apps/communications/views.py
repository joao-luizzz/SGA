from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import role_required
from .forms import ComunicadoForm
from .models import Comunicado
from .selectors import listar_comunicados_para_usuario, listar_comunicados_gerenciamento
from .services import publicar_comunicado, atualizar_comunicado, inativar_comunicado


@login_required
def mural_index(request):
    """
    Exibe o mural de comunicados vigentes filtrados para o perfil do usuário logado.
    """
    comunicados = listar_comunicados_para_usuario(request.user)
    pode_gerenciar = request.user.role in ('COORDENACAO', 'SECRETARIA') or request.user.is_superuser

    return render(request, 'communications/mural.html', {
        'comunicados': comunicados,
        'pode_gerenciar': pode_gerenciar,
    })


@login_required
def comunicado_detail(request, pk):
    """
    Visualização detalhada de um comunicado específico.
    """
    comunicados = listar_comunicados_para_usuario(request.user)
    comunicado = get_object_or_404(comunicados, id=pk)

    pode_gerenciar = request.user.role in ('COORDENACAO', 'SECRETARIA') or request.user.is_superuser

    return render(request, 'communications/comunicado_detail.html', {
        'comunicado': comunicado,
        'pode_gerenciar': pode_gerenciar,
    })


@login_required
@role_required('COORDENACAO', 'SECRETARIA')
def comunicados_gestao(request):
    """
    Painel de gestão de todos os comunicados (publicados, agendados e inativos).
    """
    comunicados = listar_comunicados_gerenciamento(request.user)
    return render(request, 'communications/comunicado_gerenciar.html', {
        'comunicados': comunicados,
    })


@login_required
@role_required('COORDENACAO', 'SECRETARIA')
def comunicado_create(request):
    """
    Publicação de novo comunicado pela Secretaria ou Coordenação.
    """
    if request.method == 'POST':
        form = ComunicadoForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                publicar_comunicado(
                    autor=request.user,
                    titulo=form.cleaned_data['titulo'],
                    conteudo=form.cleaned_data['conteudo'],
                    escopo=form.cleaned_data['escopo'],
                    papel_destino=form.cleaned_data.get('papel_destino'),
                    curso=form.cleaned_data.get('curso'),
                    turma=form.cleaned_data.get('turma'),
                    publicar_em=form.cleaned_data.get('publicar_em'),
                    expirar_em=form.cleaned_data.get('expirar_em'),
                )
                messages.success(request, _("Comunicado publicado com sucesso no mural!"))
                return redirect('communications:gestao')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for err in errors:
                        form.add_error(None if field == '__all__' else field, err)
            except PermissionDenied as e:
                form.add_error(None, str(e))
    else:
        form = ComunicadoForm(user=request.user)

    return render(request, 'communications/comunicado_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
@role_required('COORDENACAO', 'SECRETARIA')
def comunicado_update(request, pk):
    """
    Edição de um comunicado existente.
    """
    comunicado = get_object_or_404(Comunicado, id=pk)

    if request.method == 'POST':
        form = ComunicadoForm(request.POST, instance=comunicado, user=request.user)
        if form.is_valid():
            try:
                atualizar_comunicado(
                    comunicado=comunicado,
                    autor=request.user,
                    titulo=form.cleaned_data['titulo'],
                    conteudo=form.cleaned_data['conteudo'],
                    escopo=form.cleaned_data['escopo'],
                    papel_destino=form.cleaned_data.get('papel_destino'),
                    curso=form.cleaned_data.get('curso'),
                    turma=form.cleaned_data.get('turma'),
                    publicar_em=form.cleaned_data.get('publicar_em'),
                    expirar_em=form.cleaned_data.get('expirar_em'),
                    ativo=form.cleaned_data.get('ativo', True)
                )
                messages.success(request, _("Comunicado atualizado com sucesso!"))
                return redirect('communications:gestao')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for err in errors:
                        form.add_error(None if field == '__all__' else field, err)
            except PermissionDenied as e:
                form.add_error(None, str(e))
    else:
        form = ComunicadoForm(instance=comunicado, user=request.user)

    return render(request, 'communications/comunicado_form.html', {
        'form': form,
        'comunicado': comunicado,
        'is_edit': True,
    })


@login_required
@role_required('COORDENACAO', 'SECRETARIA')
def comunicado_inativar(request, pk):
    """
    Inativação rápida de um comunicado.
    """
    comunicado = get_object_or_404(Comunicado, id=pk)
    if request.method == 'POST':
        inativar_comunicado(comunicado=comunicado, autor=request.user)
        messages.success(request, _("Comunicado inativado com sucesso."))
    return redirect('communications:gestao')
