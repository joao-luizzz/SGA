from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import UserRole
from .models import Curso, Disciplina
from .forms import CursoForm, DisciplinaForm

@role_required(UserRole.COORDENACAO)
def index_view(request):
    cursos = Curso.objects.all().order_by('nome')
    disciplinas = Disciplina.objects.all().order_by('nome')
    context = {
        'title': 'Catálogo Acadêmico',
        'cursos': sorted(cursos, key=lambda c: (not c.ativo, c.nome)),  # Ativos primeiro, depois ordem alfabética
        'disciplinas': sorted(disciplinas, key=lambda d: (not d.ativo, d.nome)),
    }
    return render(request, 'academics/index.html', context)


@role_required(UserRole.COORDENACAO)
def curso_create_view(request):
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save()
            messages.success(request, _(f"Curso '{curso.nome}' criado com sucesso!"))
            return redirect('academics:index')
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = CursoForm()
    
    context = {
        'title': 'Criar Novo Curso',
        'form': form,
    }
    return render(request, 'academics/curso_form.html', context)


@role_required(UserRole.COORDENACAO)
def curso_update_view(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            curso = form.save()
            messages.success(request, _(f"Curso '{curso.nome}' atualizado com sucesso!"))
            return redirect('academics:index')
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = CursoForm(instance=curso)
    
    context = {
        'title': f"Editar Curso: {curso.nome}",
        'form': form,
        'curso': curso,
    }
    return render(request, 'academics/curso_form.html', context)


@role_required(UserRole.COORDENACAO)
@require_POST
def curso_inactivate_view(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    curso.ativo = False
    curso.save()
    
    messages.warning(request, _(f"Curso '{curso.nome}' foi inativado com sucesso."))
    
    if request.headers.get('HX-Request'):
        response = render(request, 'includes/messages.html')
        response['HX-Redirect'] = reverse('academics:index')
        return response
        
    return redirect('academics:index')


@role_required(UserRole.COORDENACAO)
def disciplina_create_view(request):
    if request.method == 'POST':
        form = DisciplinaForm(request.POST)
        if form.is_valid():
            disciplina = form.save()
            messages.success(request, _(f"Disciplina '{disciplina.nome}' criada com sucesso!"))
            return redirect('academics:index')
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = DisciplinaForm()
    
    context = {
        'title': 'Criar Nova Disciplina',
        'form': form,
    }
    return render(request, 'academics/disciplina_form.html', context)


@role_required(UserRole.COORDENACAO)
def disciplina_update_view(request, pk):
    disciplina = get_object_or_404(Disciplina, pk=pk)
    if request.method == 'POST':
        form = DisciplinaForm(request.POST, instance=disciplina)
        if form.is_valid():
            disciplina = form.save()
            messages.success(request, _(f"Disciplina '{disciplina.nome}' atualizada com sucesso!"))
            return redirect('academics:index')
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = DisciplinaForm(instance=disciplina)
    
    context = {
        'title': f"Editar Disciplina: {disciplina.nome}",
        'form': form,
        'disciplina': disciplina,
    }
    return render(request, 'academics/disciplina_form.html', context)


@role_required(UserRole.COORDENACAO)
@require_POST
def disciplina_inactivate_view(request, pk):
    disciplina = get_object_or_404(Disciplina, pk=pk)
    disciplina.ativo = False
    disciplina.save()
    
    messages.warning(request, _(f"Disciplina '{disciplina.nome}' foi inativada com sucesso."))
    
    if request.headers.get('HX-Request'):
        response = render(request, 'includes/messages.html')
        response['HX-Redirect'] = reverse('academics:index')
        return response
        
    return redirect('academics:index')
