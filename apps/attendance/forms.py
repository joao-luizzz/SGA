from django import forms
from django.utils.translation import gettext_lazy as _


class SelecionarTurmaDataForm(forms.Form):
    """Formulário para o professor selecionar turma e data de aula antes de lançar chamada."""

    turma = forms.ModelChoiceField(
        queryset=None,
        label=_('Turma'),
        empty_label=_('Selecione uma turma...'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    data_aula = forms.DateField(
        label=_('Data da Aula'),
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        ),
    )

    def __init__(self, *args, professor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if professor is not None:
            from academics.models import Turma
            self.fields['turma'].queryset = Turma.objects.filter(
                professor=professor, ativo=True
            ).select_related('disciplina').order_by('-periodo_letivo', 'disciplina__nome')


class ChamadaForm(forms.Form):
    """
    Formulário dinâmico de chamada.
    Cada aluno da turma recebe um campo BooleanField para marcar presença.
    Os campos são nomeados como 'presente_<aluno_id>'.
    """

    def __init__(self, *args, alunos=None, faltas_existentes=None, **kwargs):
        super().__init__(*args, **kwargs)
        faltas_existentes = faltas_existentes or {}

        if alunos:
            for aluno in alunos:
                campo = f'presente_{aluno.pk}'
                presente_atual = faltas_existentes.get(aluno.pk)
                # Se já existe registro, usa o valor; caso contrário, marca como presente por padrão
                valor_inicial = presente_atual if presente_atual is not None else True
                self.fields[campo] = forms.BooleanField(
                    required=False,
                    initial=valor_inicial,
                    label=aluno.full_name,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                )

    def get_presencas(self) -> dict:
        """Retorna dict {aluno_id: bool} com o resultado da chamada."""
        resultado = {}
        for nome_campo, valor in self.cleaned_data.items():
            if nome_campo.startswith('presente_'):
                aluno_id = int(nome_campo.split('_', 1)[1])
                resultado[aluno_id] = valor
        return resultado
