from django import forms

from .models import TipoAvaliacao


class LancamentoNotasTurmaForm(forms.Form):
    """Formulário dinâmico para lançamento em lote por turma."""

    def __init__(self, *args, matriculas, **kwargs):
        self.matriculas = list(matriculas)
        super().__init__(*args, **kwargs)
        for matricula in self.matriculas:
            notas = {nota.tipo: nota.valor for nota in matricula.notas.all()}
            for tipo, label in TipoAvaliacao.choices:
                self.fields[self.nome_campo(matricula.pk, tipo)] = forms.DecimalField(
                    label=label,
                    required=False,
                    min_value=0,
                    max_value=10,
                    max_digits=4,
                    decimal_places=2,
                    initial=notas.get(tipo),
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control form-control-sm',
                        'min': '0',
                        'max': '10',
                        'step': '0.01',
                        'aria-label': f'{label} de {matricula.aluno.full_name}',
                    }),
                )

    @staticmethod
    def nome_campo(matricula_id, tipo):
        return f'nota_{matricula_id}_{tipo}'

    def get_notas_preenchidas(self):
        notas_por_matricula = {}
        for matricula in self.matriculas:
            notas = {}
            for tipo in TipoAvaliacao.values:
                valor = self.cleaned_data[self.nome_campo(matricula.pk, tipo)]
                if valor is not None:
                    notas[tipo] = valor
            if notas:
                notas_por_matricula[matricula.pk] = notas
        return notas_por_matricula
