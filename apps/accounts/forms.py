from django import forms
from django.contrib.auth import password_validation
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

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            from .models import CustomUser
            try:
                user = CustomUser.objects.get(email=username)
                if not user.is_active and user.check_password(password):
                    raise forms.ValidationError(
                        self.error_messages['inactive'],
                        code='inactive',
                    )
            except CustomUser.DoesNotExist:
                pass

        return super().clean()

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

    password1 = forms.CharField(
        label=_("Senha temporária"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Confirme a senha temporária"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

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

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("As senhas não coincidem."))
        if password2:
            password_validation.validate_password(password2, self.instance)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.must_change_password = True
        if commit:
            user.save()
        return user

class AlunoCreationForm(BaseUsuarioCreationForm):
    """Formulário para criar um novo Aluno."""
    def save(self, commit=True):
        user = super().save(commit=False)
        from .models import UserRole
        user.role = UserRole.ALUNO
        if commit:
            user.save()
        return user

class ProfessorCreationForm(BaseUsuarioCreationForm):
    """Formulário para criar um novo Professor."""
    def save(self, commit=True):
        user = super().save(commit=False)
        from .models import UserRole
        user.role = UserRole.PROFESSOR
        if commit:
            user.save()
        return user


class UsuarioEditForm(forms.ModelForm):
    """Edição cadastral restrita a Alunos e Professores."""

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
        if not email:
            return email

        email_normalizado = email.strip().lower()
        from .models import CustomUser
        if CustomUser.objects.filter(email__iexact=email_normalizado).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(_("Já existe um usuário cadastrado com este e-mail."))
        return email_normalizado
