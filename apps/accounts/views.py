from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .forms import SGAAuthenticationForm, SGAMandatoryPasswordChangeForm
from .models import UserRole
from .decorators import role_required
from .selectors import get_dashboard_url_by_role
from .services import change_user_password

def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_by_role(request.user.role))

    if request.method == 'POST':
        form = SGAAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, _("Sua conta está inativa. Procure a Secretaria."))
                return render(request, 'registration/login.html', {'form': form})

            login(request, user)
            messages.success(request, _(f"Bem-vindo(a), {user.full_name}!"))

            if user.must_change_password:
                messages.warning(request, _("Por favor, altere sua senha temporária para continuar."))
                return redirect('accounts:change_password')

            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect(get_dashboard_url_by_role(user.role))
        else:
            messages.error(request, _("Credenciais inválidas. Verifique seu e-mail e senha."))
    else:
        form = SGAAuthenticationForm(request)

    return render(request, 'registration/login.html', {'form': form})

@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, _("Você saiu do sistema com segurança."))
    return redirect('accounts:login')

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = SGAMandatoryPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = change_user_password(request.user, form.cleaned_data['new_password1'])
            update_session_auth_hash(request, user)
            messages.success(request, _("Sua senha foi alterada com sucesso!"))
            return redirect(get_dashboard_url_by_role(user.role))
        else:
            messages.error(request, _("Por favor, corrija os erros no formulário abaixo."))
    else:
        form = SGAMandatoryPasswordChangeForm(user=request.user)

    return render(request, 'registration/change_password.html', {'form': form})

@login_required
def dashboard_view(request):
    return redirect(get_dashboard_url_by_role(request.user.role))

@role_required(UserRole.ALUNO)
def aluno_dashboard_view(request):
    context = {
        'title': 'Painel do Aluno',
        'role_label': 'Aluno',
    }
    return render(request, 'dashboards/aluno.html', context)

@role_required(UserRole.PROFESSOR)
def professor_dashboard_view(request):
    context = {
        'title': 'Painel do Professor',
        'role_label': 'Professor',
    }
    return render(request, 'dashboards/professor.html', context)

@role_required(UserRole.SECRETARIA)
def secretaria_dashboard_view(request):
    context = {
        'title': 'Painel da Secretaria',
        'role_label': 'Secretaria',
    }
    return render(request, 'dashboards/secretaria.html', context)

@role_required(UserRole.COORDENACAO)
def coordenacao_dashboard_view(request):
    context = {
        'title': 'Painel da Coordenação',
        'role_label': 'Coordenação',
    }
    return render(request, 'dashboards/coordenacao.html', context)

def custom_permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)

def custom_page_not_found_view(request, exception=None):
    return render(request, '404.html', status=404)

from django.shortcuts import get_object_or_404
from .selectors import list_manageable_users
from .services import toggle_user_active_status
from .forms import AlunoCreationForm, ProfessorCreationForm

@role_required(UserRole.SECRETARIA)
def usuario_list_view(request):
    usuarios = list_manageable_users()
    context = {
        'usuarios': usuarios,
        'title': 'Gerenciar Usuários (Alunos e Professores)',
    }
    return render(request, 'accounts/usuario_list.html', context)

@role_required(UserRole.SECRETARIA)
def usuario_create_view(request):
    tipo = request.GET.get('tipo', 'aluno')
    form_by_tipo = {
        'aluno': (AlunoCreationForm, "Cadastrar Aluno"),
        'professor': (ProfessorCreationForm, "Cadastrar Professor"),
    }
    if tipo not in form_by_tipo:
        return HttpResponseBadRequest(_("Tipo de usuário inválido."))

    form_class, title = form_by_tipo[tipo]

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _(f"{title.split(' ')[1]} cadastrado(a) com sucesso! A senha padrão deve ser alterada no primeiro acesso."))
            return redirect('accounts:usuario_list')
    else:
        form = form_class()

    return render(request, 'accounts/usuario_form.html', {'form': form, 'title': title, 'tipo': tipo})

@require_POST
@role_required(UserRole.SECRETARIA)
def usuario_toggle_active_view(request, user_id):
    from .models import CustomUser
    user = get_object_or_404(CustomUser, id=user_id)
    if user.pk == request.user.pk:
        messages.error(request, _("Você não pode alterar o status da própria conta."))
    elif user.role in [UserRole.ALUNO, UserRole.PROFESSOR]:
        toggle_user_active_status(user)
        status = "ativado(a)" if user.is_active else "inativado(a)"
        messages.success(request, _(f"Usuário {user.full_name} foi {status} com sucesso!"))
    else:
        messages.error(request, _("Ação não permitida para este tipo de usuário."))
    return redirect('accounts:usuario_list')
