from django import forms

from academics.models import Turma
from accounts.models import CustomUser, UserRole

from .models import Matricula
from .services import matricular_aluno_administrativo


class MatriculaAdministrativaForm(forms.ModelForm):
    """Formulário da matrícula executada pela Secretaria."""

    class Meta:
        model = Matricula
        fields = ['aluno', 'turma']
        widgets = {
            'aluno': forms.Select(attrs={'class': 'form-select'}),
            'turma': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, usuario_secretaria=None, **kwargs):
        self.usuario_secretaria = usuario_secretaria
        super().__init__(*args, **kwargs)
        self.fields['aluno'].queryset = CustomUser.objects.filter(
            role=UserRole.ALUNO,
            is_active=True,
        ).order_by('full_name')
        self.fields['turma'].queryset = Turma.objects.filter(ativo=True).select_related(
            'disciplina', 'professor'
        )

    def save(self, commit=True):
        return matricular_aluno_administrativo(
            usuario_secretaria=self.usuario_secretaria,
            aluno=self.cleaned_data['aluno'],
            turma=self.cleaned_data['turma'],
        )
