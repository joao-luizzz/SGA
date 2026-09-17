from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import UserRole
from .models import Curso, Disciplina, Turma, HorarioTurma
from .forms import CursoForm, DisciplinaForm, TurmaForm, HorarioTurmaForm

@role_required(UserRole.COORDENACAO)
def index_view(request):
    cursos = Curso.objects.all().order_by('nome')
    disciplinas = Disciplina.objects.all().order_by('nome')
    turmas = Turma.objects.all()
    context = {
        'title': 'Catálogo Acadêmico',
        'cursos': sorted(cursos, key=lambda c: (not c.ativo, c.nome)),  # Ativos primeiro, depois ordem alfabética
        'disciplinas': sorted(disciplinas, key=lambda d: (not d.ativo, d.nome)),
        'turmas': sorted(turmas, key=lambda t: (not t.ativo, t.periodo_letivo, t.disciplina.nome)),
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


@role_required(UserRole.COORDENACAO)
def turma_create_view(request):
    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    turma = form.save()
                    from academics.services import sincronizar_horarios_turma
                    sincronizar_horarios_turma(turma)
            except ValidationError as error:
                if hasattr(error, 'error_dict'):
                    for field, errors in error.message_dict.items():
                        form.add_error(field if field in form.fields else None, errors)
                else:
                    form.add_error(None, error)
                messages.error(request, _("Não foi possível criar a turma devido a um conflito de horário."))
            else:
                messages.success(request, _(f"Turma para '{turma.disciplina.nome}' no período {turma.periodo_letivo} aberta com sucesso!"))
                return redirect('academics:index')
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = TurmaForm()
    
    context = {
        'title': 'Abrir Nova Turma',
        'form': form,
    }
    return render(request, 'academics/turma_form.html', context)


@role_required(UserRole.COORDENACAO)
def turma_update_view(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            try:
                with transaction.atomic():
                    turma = form.save()
                    from academics.services import sincronizar_horarios_turma
                    sincronizar_horarios_turma(turma)
            except ValidationError as error:
                if hasattr(error, 'error_dict'):
                    for field, errors in error.message_dict.items():
                        form.add_error(field if field in form.fields else None, errors)
                else:
                    form.add_error(None, error)
                messages.error(request, _("Não foi possível atualizar a turma devido a um conflito de horário."))
            else:
                messages.success(request, _(f"Turma '{turma.disciplina.nome}' atualizada com sucesso!"))
                return redirect('academics:index')
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = TurmaForm(instance=turma)
    
    context = {
        'title': f"Editar Turma: {turma.disciplina.nome} ({turma.periodo_letivo})",
        'form': form,
        'turma': turma,
    }
    return render(request, 'academics/turma_form.html', context)


@role_required(UserRole.COORDENACAO)
@require_POST
def turma_inactivate_view(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    turma.ativo = False
    turma.save()
    
    messages.warning(request, _(f"Turma '{turma.disciplina.nome}' ({turma.periodo_letivo}) foi inativada com sucesso."))
    
    if request.headers.get('HX-Request'):
        response = render(request, 'includes/messages.html')
        response['HX-Redirect'] = reverse('academics:index')
        return response
        
    return redirect('academics:index')


@role_required(UserRole.COORDENACAO)
def turma_horarios_view(request, turma_pk):
    turma = get_object_or_404(Turma, pk=turma_pk)
    horarios = turma.horarios_aula.all().order_by('dia_semana', 'hora_inicio')
    
    if request.method == 'POST':
        form = HorarioTurmaForm(request.POST)
        if form.is_valid():
            horario = form.save(commit=False)
            horario.turma = turma
            try:
                horario.full_clean()
                horario.save()
                from academics.services import atualizar_campo_textual_turma
                atualizar_campo_textual_turma(turma)
                messages.success(request, _("Horário adicionado com sucesso!"))
                
                if request.headers.get('HX-Request'):
                    from django.http import HttpResponse
                    response = HttpResponse()
                    response['HX-Redirect'] = reverse('academics:turma_horarios', args=[turma.pk])
                    return response
                return redirect('academics:turma_horarios', turma_pk=turma.pk)
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field if field != '__all__' else None, error)
                messages.error(request, _("Não foi possível salvar o horário devido a um conflito."))
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = HorarioTurmaForm(initial={'turma': turma})
    
    if 'turma' in form.fields:
        form.fields['turma'].widget = forms.HiddenInput()
        form.fields['turma'].initial = turma.pk

    context = {
        'title': f"Grade de Horários - {turma.disciplina.nome} ({turma.periodo_letivo})",
        'turma': turma,
        'horarios': horarios,
        'form': form,
    }
    return render(request, 'academics/turma_horarios.html', context)


@role_required(UserRole.COORDENACAO)
@require_POST
def horario_delete_view(request, pk):
    horario = get_object_or_404(HorarioTurma, pk=pk)
    turma = horario.turma
    turma_pk = turma.pk
    horario.delete()
    from academics.services import atualizar_campo_textual_turma
    atualizar_campo_textual_turma(turma)
    
    messages.warning(request, _("Horário de aula removido com sucesso."))
    
    if request.headers.get('HX-Request'):
        from django.http import HttpResponse
        response = HttpResponse()
        response['HX-Redirect'] = reverse('academics:turma_horarios', args=[turma_pk])
        return response
        
    return redirect('academics:turma_horarios', turma_pk=turma_pk)


@role_required(UserRole.ALUNO, UserRole.PROFESSOR, UserRole.SECRETARIA, UserRole.COORDENACAO)
def grade_horaria_view(request):
    from datetime import time
    from django.db.models import Prefetch
    from academics.models import Curso, Turma
    
    role = request.user.role
    horarios_list = []
    
    if role == UserRole.ALUNO:
        horarios_list = HorarioTurma.objects.filter(
            turma__matriculas__aluno=request.user,
            turma__matriculas__status='ATIVA',
            turma__ativo=True
        ).select_related('turma__disciplina', 'turma__professor', 'turma__disciplina__curso')
    elif role == UserRole.PROFESSOR:
        horarios_list = HorarioTurma.objects.filter(
            turma__professor=request.user,
            turma__ativo=True
        ).select_related('turma__disciplina', 'turma__disciplina__curso')
    else:
        horarios_list = HorarioTurma.objects.filter(
            turma__ativo=True
        ).select_related('turma__disciplina', 'turma__professor', 'turma__disciplina__curso')
        
        # Filtros de curso e período para Coordenação/Secretaria
        curso_id = request.GET.get('curso')
        if curso_id:
            horarios_list = horarios_list.filter(turma__disciplina__curso_id=curso_id)
            
        periodo = request.GET.get('periodo')
        if periodo:
            horarios_list = horarios_list.filter(turma__periodo_letivo=periodo)

    DIAS_SEMANA_ORDEM = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']
    DIAS_LABELS = {
        'SEG': _('Segunda-feira'),
        'TER': _('Terça-feira'),
        'QUA': _('Quarta-feira'),
        'QUI': _('Quinta-feira'),
        'SEX': _('Sexta-feira'),
        'SAB': _('Sábado'),
        'DOM': _('Domingo'),
    }
    
    grade_por_dia = {dia: [] for dia in DIAS_SEMANA_ORDEM}
    for h in horarios_list:
        if h.dia_semana in grade_por_dia:
            grade_por_dia[h.dia_semana].append(h)
            
    for dia in grade_por_dia:
        grade_por_dia[dia].sort(key=lambda x: x.hora_inicio or time(0, 0))

    cursos = []
    periodos = []
    if role in [UserRole.SECRETARIA, UserRole.COORDENACAO]:
        cursos = Curso.objects.filter(ativo=True).order_by('nome')
        periodos = Turma.objects.filter(ativo=True).values_list('periodo_letivo', flat=True).distinct().order_by('-periodo_letivo')

    # Convertemos para lista de tuplas para iteração ordenada amigável no template
    grade_ordenada = [
        (DIAS_LABELS[dia], grade_por_dia[dia])
        for dia in DIAS_SEMANA_ORDEM
        if grade_por_dia[dia] or role in [UserRole.SECRETARIA, UserRole.COORDENACAO]
    ]

    context = {
        'title': _("Minha Grade Horária") if role in [UserRole.ALUNO, UserRole.PROFESSOR] else _("Grade Horária Geral"),
        'grade_ordenada': grade_ordenada,
        'cursos': cursos,
        'periodos': periodos,
        'selected_curso': int(curso_id) if (request.GET.get('curso') and request.GET.get('curso').isdigit()) else None,
        'selected_periodo': request.GET.get('periodo'),
        'role': role,
    }
    return render(request, 'academics/grade_horaria.html', context)


