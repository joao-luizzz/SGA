from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from communications.selectors import listar_comunicados_para_usuario, listar_destinatarios_comunicado
from .models import Notificacao, TipoNotificacao
from .selectors import listar_notificacoes


DADOS_NOTIFICACAO_COMUNICADO = {
    'titulo': 'Comunicado disponível',
    'mensagem': 'Há um comunicado disponível no mural.',
    'tipo': TipoNotificacao.COMUNICADO,
}


def _notificar_comunicado(usuario, comunicado):
    return Notificacao.objects.get_or_create(
        destinatario=usuario, comunicado=comunicado, defaults=DADOS_NOTIFICACAO_COMUNICADO,
    )[0]


@transaction.atomic
def sincronizar_comunicados(usuario):
    """Materializa agendados somente após publicação e somente para o destinatário.

    Não exige worker: a próxima visita autenticada sincroniza os comunicados vigentes.
    A constraint impede duplicação em visitas concorrentes.
    """
    if not usuario or not usuario.is_authenticated or not usuario.is_active:
        return
    existentes = Notificacao.objects.filter(
        destinatario=usuario, comunicado__isnull=False,
    ).values('comunicado_id')
    for comunicado in listar_comunicados_para_usuario(usuario).exclude(pk__in=existentes):
        _notificar_comunicado(usuario, comunicado)


def notificar_comunicado(comunicado):
    """Chamado dentro da transação do evento; rollback desfaz ambos os registros.

    O público é calculado em lote e as notificações são criadas com um único
    INSERT; a constraint destinatário+comunicado ignora quem já foi notificado.
    """
    destinatarios = listar_destinatarios_comunicado(comunicado).values_list('pk', flat=True)
    Notificacao.objects.bulk_create(
        [Notificacao(destinatario_id=pk, comunicado=comunicado, **DADOS_NOTIFICACAO_COMUNICADO)
         for pk in destinatarios],
        ignore_conflicts=True,
    )


def notificar_evento_academico(*, destinatario, tipo):
    if not destinatario.is_active:
        return None
    titulo = 'Nota atualizada' if tipo == TipoNotificacao.NOTA else 'Frequência atualizada'
    return Notificacao.objects.create(
        destinatario=destinatario, tipo=tipo, titulo=titulo,
        mensagem='Um registro acadêmico foi lançado ou alterado. Consulte seu boletim.',
    )


@transaction.atomic
def marcar_como_lida(usuario, pk):
    notificacao = get_object_or_404(listar_notificacoes(usuario), pk=pk)
    listar_notificacoes(usuario).filter(pk=pk, lida_em__isnull=True).update(lida_em=timezone.now())
    return notificacao


@transaction.atomic
def marcar_todas_como_lidas(usuario):
    sincronizar_comunicados(usuario)
    return listar_notificacoes(usuario).filter(lida_em__isnull=True).update(lida_em=timezone.now())
