from django.db.models import Count, Q, Sum
from django.utils import timezone

from accounts.models import UserRole

from .models import Cobranca, StatusCobranca

FILTRO_ATRASO = 'ATRASO'


def listar_cobrancas(usuario, status=''):
    """Aluno vê somente as próprias cobranças (RN25); Secretaria e superusuário veem todas."""
    cobrancas = Cobranca.objects.select_related('aluno', 'registrado_por')
    if not usuario.is_superuser and usuario.role == UserRole.ALUNO:
        cobrancas = cobrancas.filter(aluno=usuario)
    elif not usuario.is_superuser and usuario.role != UserRole.SECRETARIA:
        return cobrancas.none()
    if status == FILTRO_ATRASO:
        cobrancas = cobrancas.filter(status=StatusCobranca.ABERTA, vencimento__lt=timezone.localdate())
    elif status:
        cobrancas = cobrancas.filter(status=status)
    return cobrancas


def resumir_cobrancas(cobrancas):
    """Totais em aberto e em atraso de um queryset de cobranças."""
    hoje = timezone.localdate()
    abertas = Q(status=StatusCobranca.ABERTA)
    atrasadas = abertas & Q(vencimento__lt=hoje)
    resumo = cobrancas.order_by().aggregate(
        total_aberto=Sum('valor', filter=abertas),
        quantidade_atraso=Count('pk', filter=atrasadas),
        total_atraso=Sum('valor', filter=atrasadas),
    )
    resumo['total_aberto'] = resumo['total_aberto'] or 0
    resumo['total_atraso'] = resumo['total_atraso'] or 0
    return resumo
