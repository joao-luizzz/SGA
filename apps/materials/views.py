from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from academics.models import Turma
from accounts.decorators import role_required
from .forms import MaterialForm
from .models import MaterialAcademico
from .selectors import get_turmas_para_materiais, listar_materiais_turma, usuario_pode_acessar_turma
from .services import criar_material, atualizar_material, excluir_material


@login_required
def turma_materiais_index(request):
    """
    Lista as turmas disponíveis para o usuário visualizar ou gerenciar materiais.
    """
    turmas = get_turmas_para_materiais(request.user)
    return render(request, 'materials/turmas_index.html', {
        'turmas': turmas,
    })


@login_required
def turma_materiais_list(request, turma_id):
    """
    Lista todos os materiais de uma turma específica.
    """
    turma = get_object_or_404(Turma.objects.select_related('disciplina', 'professor'), id=turma_id)
    try:
        materiais = listar_materiais_turma(turma, request.user)
    except PermissionDenied:
        raise PermissionDenied(_("Você não tem permissão para acessar os materiais desta turma."))

    pode_gerenciar = (
        request.user.role == 'COORDENACAO' or
        (request.user.role == 'PROFESSOR' and turma.professor_id == request.user.id) or
        request.user.is_superuser
    )

    return render(request, 'materials/turma_materiais.html', {
        'turma': turma,
        'materiais': materiais,
        'pode_gerenciar': pode_gerenciar,
    })


@login_required
@role_required('PROFESSOR', 'COORDENACAO')
def material_create(request, turma_id):
    """
    Publica um novo material acadêmico na turma.
    """
    turma = get_object_or_404(Turma.objects.select_related('disciplina', 'professor'), id=turma_id)

    if request.user.role == 'PROFESSOR' and turma.professor_id != request.user.id:
        raise PermissionDenied(_("Você só pode publicar materiais nas turmas sob sua responsabilidade."))

    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                criar_material(
                    turma=turma,
                    autor=request.user,
                    titulo=form.cleaned_data['titulo'],
                    descricao=form.cleaned_data['descricao'],
                    arquivo=form.cleaned_data.get('arquivo'),
                    link=form.cleaned_data.get('link'),
                )
                messages.success(request, _("Material acadêmico publicado com sucesso!"))
                return redirect('materials:turma_materiais', turma_id=turma.id)
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for err in errors:
                        form.add_error(None if field == '__all__' else field, err)
    else:
        form = MaterialForm()

    return render(request, 'materials/material_form.html', {
        'form': form,
        'turma': turma,
        'is_edit': False,
    })


@login_required
@role_required('PROFESSOR', 'COORDENACAO')
def material_update(request, pk):
    """
    Edita um material acadêmico existente.
    """
    material = get_object_or_404(MaterialAcademico.objects.select_related('turma'), id=pk)

    if request.user.role == 'PROFESSOR' and material.turma.professor_id != request.user.id:
        raise PermissionDenied(_("Você só pode editar materiais de suas próprias turmas."))

    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            try:
                atualizar_material(
                    material=material,
                    autor=request.user,
                    titulo=form.cleaned_data['titulo'],
                    descricao=form.cleaned_data['descricao'],
                    arquivo=form.cleaned_data.get('arquivo'),
                    link=form.cleaned_data.get('link'),
                )
                messages.success(request, _("Material acadêmico atualizado com sucesso!"))
                return redirect('materials:turma_materiais', turma_id=material.turma_id)
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for err in errors:
                        form.add_error(None if field == '__all__' else field, err)
    else:
        form = MaterialForm(instance=material)

    return render(request, 'materials/material_form.html', {
        'form': form,
        'turma': material.turma,
        'material': material,
        'is_edit': True,
    })


@login_required
@role_required('PROFESSOR', 'COORDENACAO')
def material_delete(request, pk):
    """
    Exclui um material acadêmico.
    """
    material = get_object_or_404(MaterialAcademico.objects.select_related('turma'), id=pk)
    turma_id = material.turma_id

    if request.user.role == 'PROFESSOR' and material.turma.professor_id != request.user.id:
        raise PermissionDenied(_("Você só pode excluir materiais de suas próprias turmas."))

    if request.method == 'POST':
        excluir_material(material=material, autor=request.user)
        messages.success(request, _("Material acadêmico excluído com sucesso!"))
        return redirect('materials:turma_materiais', turma_id=turma_id)

    return render(request, 'materials/material_confirm_delete.html', {
        'material': material,
    })
