from typing import Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from accounts.models import AcaoAuditoria, UserRole
from accounts.services import registrar_auditoria
from academics.models import Turma
from .models import Falta


def _representacao_falta(falta: Optional[Falta]) -> Optional[str]:
    """Gera uma string descritiva de um registro de Falta para auditoria."""
    if falta is None:
        return None
    situacao = 'Presente' if falta.presente else 'Ausente'
    return f"Falta #{falta.pk} | Aluno: {falta.aluno.full_name} | Turma: {falta.turma_id} | Data: {falta.data_aula} | {situacao}"


@transaction.atomic
def registrar_chamada(professor, turma, data_aula: str, presencas: dict) -> list:
    """
    Registra ou atualiza a chamada de uma turma em uma data (RN21).

    Args:
        professor: CustomUser com role=PROFESSOR responsável pelo lançamento.
        turma: Turma onde a chamada é realizada.
        data_aula: Data da aula (string no formato YYYY-MM-DD ou objeto date).
        presencas: dict {aluno_id: bool} indicando presença de cada aluno.

    Returns:
        Lista de objetos Falta criados ou atualizados.
    """
    from enrollment.models import Matricula, StatusMatricula

    if getattr(professor, 'role', None) != UserRole.PROFESSOR:
        raise ValidationError(_("A chamada deve ser registrada por um Professor."))

    turma_bloqueada = Turma.objects.select_for_update().get(pk=turma.pk)
    if not turma_bloqueada.ativo:
        raise ValidationError(_("A chamada só pode ser registrada para turma ativa."))

    if turma_bloqueada.professor_id != getattr(professor, 'pk', None):
        raise ValidationError(
            _("Somente o professor responsável pela turma pode registrar a chamada.")
        )

    try:
        presencas_normalizadas = {}
        for aluno_id, presente in presencas.items():
            aluno_id_normalizado = int(aluno_id)
            if aluno_id_normalizado in presencas_normalizadas:
                raise ValueError
            presencas_normalizadas[aluno_id_normalizado] = presente
    except (TypeError, ValueError, AttributeError):
        raise ValidationError(_("A lista de alunos informada é inválida."))

    aluno_ids = set(presencas_normalizadas)
    matriculas_ativas = list(
        Matricula.objects.select_for_update()
        .filter(
            turma=turma_bloqueada,
            status=StatusMatricula.ATIVA,
        )
        .only('aluno_id')
    )
    alunos_com_matricula_ativa = {
        matricula.aluno_id for matricula in matriculas_ativas
    }
    if aluno_ids != alunos_com_matricula_ativa:
        raise ValidationError(
            _("A chamada deve informar exatamente todos os alunos com matrícula ativa nesta turma.")
        )

    resultados = []

    for aluno_id, presente in presencas_normalizadas.items():
        valor_antigo = None
        acao = AcaoAuditoria.CRIAR

        # Tenta recuperar registro existente para auditoria
        falta_existente = Falta.objects.filter(
            turma=turma_bloqueada,
            aluno_id=aluno_id,
            data_aula=data_aula,
        ).first()

        if falta_existente:
            if (
                falta_existente.presente == presente
                and falta_existente.registrado_por_id == professor.pk
            ):
                resultados.append(falta_existente)
                continue
            valor_antigo = _representacao_falta(falta_existente)
            acao = AcaoAuditoria.EDITAR
            falta_existente.presente = presente
            falta_existente.registrado_por = professor
            falta_existente.save(update_fields=['presente', 'registrado_por'])
            falta = falta_existente
        else:
            falta = Falta.objects.create(
                turma=turma_bloqueada,
                aluno_id=aluno_id,
                data_aula=data_aula,
                presente=presente,
                registrado_por=professor,
            )

        valor_novo = _representacao_falta(falta)

        # Auditoria (RN30)
        registrar_auditoria(
            usuario=professor,
            tabela_afetada='Falta',
            registro_id=falta.pk,
            acao=acao,
            valor_antigo=valor_antigo,
            valor_novo=valor_novo,
        )

        resultados.append(falta)

    return resultados
