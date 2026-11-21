from accounts.models import UserRole

from .models import DocumentoEmitido


def listar_documentos(usuario):
    """Aluno vê somente os próprios documentos; Secretaria e superusuário veem todos."""
    documentos = DocumentoEmitido.objects.select_related('aluno', 'emitido_por')
    if usuario.is_superuser or usuario.role == UserRole.SECRETARIA:
        return documentos
    if usuario.role == UserRole.ALUNO:
        return documentos.filter(aluno=usuario)
    return documentos.none()
