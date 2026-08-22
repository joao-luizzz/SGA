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

class BaseUsuarioCreationForm(forms.ModelForm):
    """Formulário base para criação de usuários pela Secretaria."""
    class Meta:
        from .models import CustomUser
        model = CustomUser
        fields = ['full_name', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@instituicao.edu.br'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            from .models import CustomUser
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError(_("Já existe um usuário cadastrado com este e-mail."))
        return email

class AlunoCreationForm(BaseUsuarioCreationForm):
    """Formulário para criar um novo Aluno."""
    def save(self, commit=True):
        user = super().save(commit=False)
        from .models import UserRole
        user.role = UserRole.ALUNO
        user.must_change_password = True
        if commit:
            user.save()
        return user

class ProfessorCreationForm(BaseUsuarioCreationForm):
    """Formulário para criar um novo Professor."""
    def save(self, commit=True):
        user = super().save(commit=False)
        from .models import UserRole
        user.role = UserRole.PROFESSOR
        user.must_change_password = True
        if commit:
            user.save()
        return user
