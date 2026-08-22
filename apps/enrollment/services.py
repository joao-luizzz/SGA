from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from .models import Matricula, StatusMatricula
from apps.accounts.models import CustomUser
from apps.academics.models import Turma

@transaction.atomic
def matricular_aluno_administrativo(usuario_secretaria: CustomUser, aluno: CustomUser, turma: Turma) -> Matricula:
    """
    Realiza a matrícula de um aluno em uma turma por um usuário administrativo (Secretaria).
    
    Regras de Negócio:
    - Somente Secretaria matricula.
    - O usuário 'aluno' deve ter perfil ALUNO.
    - A turma deve ter vagas disponíveis.
    - Não permite duplicidade (mesmo aluno na mesma turma).
    - Se a matrícula já existir e estiver cancelada/trancada, reativa a matrícula.
    """
    if usuario_secretaria.role != 'SECRETARIA':
        raise ValidationError(_("Apenas usuários com perfil de Secretaria podem realizar matrículas administrativas."))

    if aluno.role != 'ALUNO':
        raise ValidationError(_("O usuário selecionado não tem perfil de ALUNO."))

    # Verifica se já existe uma matrícula
    matricula_existente = Matricula.objects.filter(aluno=aluno, turma=turma).first()

    if matricula_existente:
        if matricula_existente.status == StatusMatricula.ATIVA:
            raise ValidationError(_("O aluno já possui uma matrícula ATIVA nesta turma."))
        
        # Tenta reativar
        if turma.vagas_disponiveis <= 0:
            raise ValidationError(_("A turma selecionada não possui vagas disponíveis para reativar a matrícula."))
        
        matricula_existente.status = StatusMatricula.ATIVA
        matricula_existente.save()
        return matricula_existente

    # Matrícula nova
    if turma.vagas_disponiveis <= 0:
        raise ValidationError(_("A turma selecionada não possui vagas disponíveis."))

    matricula = Matricula(aluno=aluno, turma=turma, status=StatusMatricula.ATIVA)
    # Chama o clean() para garantir as validações de modelo também
    matricula.clean()
    matricula.save()
    
    return matricula
