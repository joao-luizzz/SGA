import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import AcaoAuditoria, CustomUser, UserRole
from accounts.services import registrar_auditoria

from .models import Cobranca, StatusCobranca


def _exigir_secretaria(usuario):
    if not getattr(usuario, 'is_authenticated', False) or not usuario.is_active:
        raise PermissionDenied("Autentique-se para operar cobranças.")
    if not usuario.is_superuser and usuario.role != UserRole.SECRETARIA:
        raise PermissionDenied("Somente a Secretaria opera cobranças.")


def _estado(cobranca):
    return json.dumps({
        'aluno_id': cobranca.aluno_id,
        'competencia': cobranca.competencia,
        'descricao': cobranca.descricao,
        'valor': str(cobranca.valor),
        'vencimento': str(cobranca.vencimento),
        'status': cobranca.status,
        'pago_em': cobranca.pago_em.isoformat() if cobranca.pago_em else None,
        'justificativa': cobranca.justificativa,
    }, ensure_ascii=False, sort_keys=True)


@transaction.atomic
def lancar_cobranca(*, usuario, aluno, competencia, descricao, valor, vencimento):
    _exigir_secretaria(usuario)
    aluno = CustomUser.objects.select_for_update().get(pk=aluno.pk)
    if aluno.role != UserRole.ALUNO or not aluno.is_active:
        raise ValidationError({'aluno': "Selecione um aluno ativo."})
    descricao = (descricao or '').strip()
    duplicada = Cobranca.objects.filter(
        aluno=aluno, competencia=competencia, descricao=descricao,
    ).exclude(status=StatusCobranca.CANCELADA)
    if duplicada.exists():
        raise ValidationError("Já existe cobrança não cancelada com esta descrição e competência para o aluno.")
    cobranca = Cobranca(aluno=aluno, competencia=competencia, descricao=descricao,
                        valor=valor, vencimento=vencimento, registrado_por=usuario)
    cobranca.full_clean()
    try:
        with transaction.atomic():
            cobranca.save()
    except IntegrityError as exc:
        raise ValidationError(
            "Já existe cobrança não cancelada com esta descrição e competência para o aluno."
        ) from exc
    registrar_auditoria(usuario=usuario, tabela_afetada='Cobranca', registro_id=cobranca.pk,
                        acao=AcaoAuditoria.CRIAR, valor_novo=_estado(cobranca))
    return cobranca


def _transicionar(*, usuario, cobranca_id, **campos):
    cobranca = Cobranca.objects.select_for_update().get(pk=cobranca_id)
    if cobranca.status != StatusCobranca.ABERTA:
        raise ValidationError("Somente cobranças abertas podem ser baixadas ou canceladas.")
    anterior = _estado(cobranca)
    # Compare-and-set: barreira adicional contra duas transições concorrentes.
    alteradas = Cobranca.objects.filter(pk=cobranca.pk, status=StatusCobranca.ABERTA).update(**campos)
    if alteradas != 1:
        raise ValidationError("Esta cobrança já foi alterada por outro usuário.")
    cobranca.refresh_from_db()
    registrar_auditoria(usuario=usuario, tabela_afetada='Cobranca', registro_id=cobranca.pk,
                        acao=AcaoAuditoria.EDITAR, valor_antigo=anterior, valor_novo=_estado(cobranca))
    return cobranca


@transaction.atomic
def registrar_pagamento(*, usuario, cobranca_id):
    _exigir_secretaria(usuario)
    return _transicionar(usuario=usuario, cobranca_id=cobranca_id,
                         status=StatusCobranca.PAGA, pago_em=timezone.now())


@transaction.atomic
def cancelar_cobranca(*, usuario, cobranca_id, justificativa):
    _exigir_secretaria(usuario)
    justificativa = (justificativa or '').strip()
    if not justificativa or len(justificativa) > 1000:
        raise ValidationError({'justificativa': "Informe uma justificativa entre 1 e 1000 caracteres."})
    return _transicionar(usuario=usuario, cobranca_id=cobranca_id,
                         status=StatusCobranca.CANCELADA, justificativa=justificativa)
