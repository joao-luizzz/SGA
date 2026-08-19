from typing import Optional
from django.db import transaction
from accounts.models import AcaoAuditoria
from accounts.services import registrar_auditoria
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
    from enrollment.selectors import get_matriculas_ativas_da_turma

    resultados = []

    for aluno_id, presente in presencas.items():
        valor_antigo = None
        acao = AcaoAuditoria.CRIAR

        # Tenta recuperar registro existente para auditoria
        falta_existente = Falta.objects.filter(
            turma=turma,
            aluno_id=aluno_id,
            data_aula=data_aula,
        ).first()

        if falta_existente:
            valor_antigo = _representacao_falta(falta_existente)
            acao = AcaoAuditoria.EDITAR
            falta_existente.presente = presente
            falta_existente.registrado_por = professor
            falta_existente.save(update_fields=['presente', 'registrado_por'])
            falta = falta_existente
        else:
            falta = Falta.objects.create(
                turma=turma,
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
