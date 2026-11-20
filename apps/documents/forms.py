from django import forms

from accounts.models import CustomUser, UserRole

from .models import TipoDocumento


class EmissaoForm(forms.Form):
    tipo = forms.ChoiceField(
        label='Documento', choices=TipoDocumento.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    aluno = forms.ModelChoiceField(
        label='Aluno', required=False,
        queryset=CustomUser.objects.filter(role=UserRole.ALUNO).order_by('full_name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class VerificacaoForm(forms.Form):
    codigo = forms.CharField(
        label='Código de verificação', max_length=40,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXXX-XXXX-XXXX-XXXX',
                                      'autocomplete': 'off'}),
    )
