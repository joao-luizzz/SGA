from accounts.models import UserRole

from .models import SolicitacaoTransferencia
from .permissions import PAPEIS_CONSULTA, exigir_perfil


def listar_transferencias(*, usuario, status='', tipo='', curso_id=None):
    """Aplica o escopo de acesso antes de qualquer filtro fornecido pelo cliente."""
    usuario = exigir_perfil(usuario, *PAPEIS_CONSULTA)
    registros = SolicitacaoTransferencia.objects.select_related(
        'aluno', 'curso', 'solicitada_por', 'analisada_por',
    )
    if usuario.role == UserRole.ALUNO and not usuario.is_superuser:
        registros = registros.filter(aluno=usuario)
    if status:
        registros = registros.filter(status=status)
    if tipo:
        registros = registros.filter(tipo=tipo)
    if curso_id:
        registros = registros.filter(curso_id=curso_id)
    return registros
