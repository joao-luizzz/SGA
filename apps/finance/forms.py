from django import forms

from accounts.models import CustomUser, UserRole

from .selectors import FILTRO_ATRASO


class CobrancaForm(forms.Form):
    aluno = forms.ModelChoiceField(
        label='Aluno',
        queryset=CustomUser.objects.filter(role=UserRole.ALUNO, is_active=True).order_by('full_name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    competencia = forms.RegexField(
        label='Competência (AAAA-MM)', regex=r'^\d{4}-(0[1-9]|1[0-2])$',
        error_messages={'invalid': 'Use o formato AAAA-MM.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2026-11'}),
    )
    descricao = forms.CharField(
        label='Descrição', max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mensalidade'}),
    )
    valor = forms.DecimalField(
        label='Valor (R$)', min_value=0.01, max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    vencimento = forms.DateField(
        label='Vencimento', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )


class CancelamentoForm(forms.Form):
    justificativa = forms.CharField(
        label='Justificativa do cancelamento', max_length=1000,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )


class FiltroCobrancaForm(forms.Form):
    status = forms.ChoiceField(
        label='Situação', required=False,
        choices=[('', 'Todas'), ('ABERTA', 'Aberta'), (FILTRO_ATRASO, 'Em atraso'),
                 ('PAGA', 'Paga'), ('CANCELADA', 'Cancelada')],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
