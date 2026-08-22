from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Matricula
from .services import matricular_aluno_administrativo

class MatriculaAdministrativaForm(forms.ModelForm):
    """
    Formulário para a Secretaria realizar a matrícula de um aluno em uma turma.
    As validações de limite de vagas e duplicidade são tratadas no service.
    """
    class Meta:
        model = Matricula
        fields = ['aluno', 'turma']
    
    def __init__(self, *args, **kwargs):
        self.usuario_secretaria = kwargs.pop('usuario_secretaria', None)
        super().__init__(*args, **kwargs)
        # Filtra alunos e turmas ativas, se necessário, na view
        
    def save(self, commit=True):
        aluno = self.cleaned_data.get('aluno')
        turma = self.cleaned_data.get('turma')
        
        # Delega a lógica de criação e regras de negócio para o Service
        # O service já retorna a matrícula (criada ou reativada)
        return matricular_aluno_administrativo(
            usuario_secretaria=self.usuario_secretaria,
            aluno=aluno,
            turma=turma
        )
