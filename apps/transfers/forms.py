from django import forms
from django.utils import timezone

from academics.models import Curso
from accounts.models import CustomUser, UserRole
from .models import TipoTransferencia, StatusTransferencia


class BootstrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs['class'] = 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control'


class SolicitacaoTransferenciaForm(BootstrapForm):
    aluno = forms.ModelChoiceField(queryset=CustomUser.objects.none(), label='Aluno')
    curso = forms.ModelChoiceField(queryset=Curso.objects.none(), label='Curso na instituição atual')
    tipo = forms.ChoiceField(choices=TipoTransferencia.choices, label='Tipo')
    instituicao_externa = forms.CharField(max_length=200, label='Instituição externa')
    curso_externo = forms.CharField(max_length=200, label='Curso na instituição externa')
    data_referencia = forms.DateField(
        label='Data de referência da transferência', initial=timezone.localdate,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
    )
    documentos = forms.CharField(
        max_length=3000, label='Registro dos documentos', widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Liste os documentos apresentados ou justifique sua dispensa. Não há envio de arquivos nesta etapa.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['aluno'].queryset = CustomUser.objects.filter(role=UserRole.ALUNO, is_active=True).order_by('full_name', 'pk')
        self.fields['curso'].queryset = Curso.objects.filter(ativo=True).order_by('nome', 'pk')


class AnaliseTransferenciaForm(BootstrapForm):
    decisao = forms.ChoiceField(
        label='Decisão', choices=[('', 'Selecione uma decisão'),
                                  (StatusTransferencia.APROVADA, 'Aprovar'),
                                  (StatusTransferencia.RECUSADA, 'Recusar')],
    )
    justificativa = forms.CharField(
        max_length=3000, label='Justificativa da decisão', widget=forms.Textarea(attrs={'rows': 4}),
    )


class FiltroTransferenciaForm(BootstrapForm):
    status = forms.ChoiceField(label='Situação', required=False, choices=[('', 'Todas')] + StatusTransferencia.choices)
    tipo = forms.ChoiceField(label='Tipo', required=False, choices=[('', 'Todos')] + TipoTransferencia.choices)
    curso = forms.IntegerField(label='Código interno do curso (ID)', min_value=1, required=False)
