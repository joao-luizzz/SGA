from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from .models import Matricula, StatusMatricula
from apps.accounts.models import CustomUser
from apps.academics.models import Turma

@transaction.atomic
def matricular_aluno_administrativo(usuario_secretaria: CustomUser, aluno: CustomUser, turma: Turma) -> Matricula:
    """
    Realiza a matrícula de um aluno em uma turma específica, executada exclusivamente
    por um usuário com perfil administrativo (Secretaria).
    
    Regras de Negócio e Validações:
    - RN_MAT_01: O usuário executor deve ter `role == 'SECRETARIA'`.
    - RN_MAT_02: O usuário alvo (`aluno`) deve obrigatoriamente possuir `role == 'ALUNO'`.
    - RN_MAT_03: A `Turma` selecionada deve ter vagas disponíveis (`vagas_disponiveis > 0`).
    - RN_MAT_04: Impede a duplicidade de matrícula ativa (mesmo aluno na mesma turma).
    - RN_MAT_05: Se a matrícula já existir, porém cancelada ou trancada, o sistema tenta reativá-la
                 (alterando o status para ATIVA), desde que haja vagas na turma.

    :param usuario_secretaria: Instância de CustomUser representando a secretaria.
    :param aluno: Instância de CustomUser representando o aluno.
    :param turma: Instância de Turma na qual o aluno será matriculado.
    :return: A instância da Matricula criada ou reativada.
    :raises ValidationError: Caso qualquer regra de negócio seja violada.
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
