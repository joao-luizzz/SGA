from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _

class SGAAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("E-mail"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@sga.edu.br',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_("Senha"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )

    error_messages = {
        'invalid_login': _("E-mail ou senha incorretos. Por favor, verifique suas credenciais."),
        'inactive': _("Esta conta de usuário está inativa. Procure a Secretaria."),
    }

class SGAMandatoryPasswordChangeForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("Nova Senha"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nova senha (mínimo 8 caracteres)'}),
        help_text=_("A senha deve conter pelo menos 8 caracteres.")
    )
    new_password2 = forms.CharField(
        label=_("Confirme a Nova Senha"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a nova senha'})
    )
