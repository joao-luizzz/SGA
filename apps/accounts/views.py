from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(get_dashboard_url_by_role(user.role))
        else:
            messages.error(request, _("Credenciais inválidas. Verifique seu e-mail e senha."))
    else:
        form = SGAAuthenticationForm(request)

    return render(request, 'registration/login.html', {'form': form})

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
