from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _

from academics.models import Turma
from accounts.models import CustomUser, UserRole

from .models import Matricula, StatusMatricula


@transaction.atomic
def alterar_status_matricula_administrativa(
    usuario_secretaria: CustomUser,
    matricula_id: int,
    novo_status: str,
) -> Matricula:
    """Altera definitivamente o status de uma matrícula ativa pela Secretaria."""
    if usuario_secretaria.role != UserRole.SECRETARIA:
        raise ValidationError(
            _("Apenas usuários com perfil de Secretaria podem alterar matrículas.")
        )

    statuses_permitidos = {
        StatusMatricula.TRANCADA,
        StatusMatricula.CANCELADA,
        StatusMatricula.CONCLUIDA,
    }
    if novo_status not in statuses_permitidos:
        raise ValidationError(_("O status informado não é permitido para esta operação."))

    matricula = Matricula.objects.select_for_update().get(pk=matricula_id)
    if matricula.status != StatusMatricula.ATIVA:
        raise ValidationError(_("Apenas matrículas ativas podem ter o status alterado."))

    matricula.status = novo_status
    matricula.save(update_fields=['status'])
    return matricula


@transaction.atomic
def matricular_aluno_administrativo(
    usuario_secretaria: CustomUser,
    aluno: CustomUser,
    turma: Turma,
) -> Matricula:
    """Cria uma matrícula ativa com validações e bloqueio de concorrência."""
    if usuario_secretaria.role != UserRole.SECRETARIA:
        raise ValidationError(
            _("Apenas usuários com perfil de Secretaria podem realizar matrículas administrativas.")
        )
    if aluno.role != UserRole.ALUNO or not aluno.is_active:
        raise ValidationError(_("O aluno selecionado deve possuir perfil de Aluno e estar ativo."))

    turma_bloqueada = Turma.objects.select_for_update().get(pk=turma.pk)
    if not turma_bloqueada.pode_receber_matricula():
        raise ValidationError(
            _("A turma deve estar ativa e possuir professor, horário, sala e vagas configurados.")
        )

    if Matricula.objects.filter(
        aluno=aluno,
        turma=turma_bloqueada,
        status=StatusMatricula.ATIVA,
    ).exists():
        raise ValidationError(_("O aluno já possui uma matrícula ativa nesta turma."))

    vagas_ocupadas = Matricula.objects.filter(
        turma=turma_bloqueada,
        status=StatusMatricula.ATIVA,
    ).count()
    if vagas_ocupadas >= turma_bloqueada.vagas_maximas:
        raise ValidationError(_("A turma selecionada não possui vagas disponíveis."))

    try:
        with transaction.atomic():
            return Matricula.objects.create(
                aluno=aluno,
                turma=turma_bloqueada,
                status=StatusMatricula.ATIVA,
            )
    except IntegrityError as exc:
        raise ValidationError(
            _("O aluno já possui uma matrícula ativa nesta turma.")
        ) from exc
