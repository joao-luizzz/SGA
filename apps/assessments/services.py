from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from accounts.models import AcaoAuditoria, UserRole
from accounts.services import registrar_auditoria
from academics.models import Turma
from enrollment.models import Matricula, StatusMatricula

from .models import Nota, TipoAvaliacao
from .selectors import pode_realizar_exame


def _normalizar_valor(valor):
    try:
        valor = Decimal(str(valor)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(_('Informe uma nota numérica válida.')) from exc
    if not Decimal('0.00') <= valor <= Decimal('10.00'):
        raise ValidationError(_('A nota deve estar entre 0,00 e 10,00.'))
    return valor


def _representacao_nota(nota):
    return (
        f'Nota #{nota.pk} | Matrícula: {nota.matricula_id} | '
        f'Tipo: {nota.tipo} | Valor: {nota.valor}'
    )


def _salvar_nota(professor, matricula, tipo, valor):
    nota = Nota.objects.filter(matricula=matricula, tipo=tipo).first()
    if nota is None:
        nota = Nota.objects.create(
            matricula=matricula,
            tipo=tipo,
            valor=valor,
            registrado_por=professor,
        )
        registrar_auditoria(
            usuario=professor,
            tabela_afetada='Nota',
            registro_id=nota.pk,
            acao=AcaoAuditoria.CRIAR,
            valor_novo=_representacao_nota(nota),
        )
        return nota

    if nota.valor == valor:
        return nota

    valor_antigo = _representacao_nota(nota)
    nota.valor = valor
    nota.registrado_por = professor
    nota.save(update_fields=['valor', 'registrado_por', 'atualizado_em'])
    registrar_auditoria(
        usuario=professor,
        tabela_afetada='Nota',
        registro_id=nota.pk,
        acao=AcaoAuditoria.EDITAR,
        valor_antigo=valor_antigo,
        valor_novo=_representacao_nota(nota),
    )
    return nota


@transaction.atomic
def lancar_notas_em_lote(professor, turma, notas_por_matricula):
    """Cria/edita notas de uma turma atomicamente e registra auditoria."""
    if getattr(professor, 'role', None) != UserRole.PROFESSOR:
        raise ValidationError(_('Apenas professores podem lançar notas.'))

    turma = Turma.objects.select_for_update().get(pk=turma.pk)
    if not turma.ativo or turma.professor_id != professor.pk:
        raise ValidationError(
            _('Somente o professor responsável por uma turma ativa pode lançar ou editar notas.')
        )

    try:
        ids = {int(matricula_id) for matricula_id in notas_por_matricula}
    except (TypeError, ValueError) as exc:
        raise ValidationError(_('A lista de matrículas informada é inválida.')) from exc

    matriculas = {
        matricula.pk: matricula
        for matricula in Matricula.objects.select_for_update().filter(
            pk__in=ids,
            turma=turma,
            status=StatusMatricula.ATIVA,
        ).select_related('aluno', 'turma')
    }
    if set(matriculas) != ids:
        raise ValidationError(
            _('Todas as notas devem pertencer a matrículas ativas desta turma.')
        )

    tipos_validos = set(TipoAvaliacao.values)
    dados_normalizados = {}
    for matricula_id, notas in notas_por_matricula.items():
        matricula_id = int(matricula_id)
        dados_normalizados[matricula_id] = {}
        for tipo, valor in notas.items():
            if tipo not in tipos_validos:
                raise ValidationError(_('Tipo de avaliação inválido: %(tipo)s.') % {'tipo': tipo})
            dados_normalizados[matricula_id][tipo] = _normalizar_valor(valor)

    resultados = []
    tipos_parciais = (TipoAvaliacao.P1, TipoAvaliacao.P2, TipoAvaliacao.TRABALHO)
    for matricula_id, notas in dados_normalizados.items():
        matricula = matriculas[matricula_id]
        for tipo in tipos_parciais:
            if tipo in notas:
                resultados.append(_salvar_nota(professor, matricula, tipo, notas[tipo]))

        if TipoAvaliacao.EXAME in notas:
            if not pode_realizar_exame(matricula):
                raise ValidationError(
                    _('%(aluno)s não está elegível para o Exame Final.') % {
                        'aluno': matricula.aluno.full_name,
                    }
                )
            resultados.append(
                _salvar_nota(
                    professor,
                    matricula,
                    TipoAvaliacao.EXAME,
                    notas[TipoAvaliacao.EXAME],
                )
            )

    return resultados
