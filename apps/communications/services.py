from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Comunicado, EscopoComunicado


def _validar_permissao_publicador(autor, escopo):
    """
    Valida se o usuário tem permissão de acordo com o escopo do comunicado:
    - Secretaria: comunicados GERAL e PAPEL
    - Coordenação: comunicados CURSO, TURMA e GERAL/PAPEL
    - Superuser: todos
    """
    if autor.is_superuser:
        return True

    if autor.role == 'SECRETARIA':
        if escopo in (EscopoComunicado.GERAL, EscopoComunicado.PAPEL):
            return True
        raise PermissionDenied("A Secretaria só tem permissão para emitir comunicados Gerais e por Perfil.")

    if autor.role == 'COORDENACAO':
        return True

    raise PermissionDenied("Seu perfil não possui permissão para publicar comunicados no mural.")


@transaction.atomic
def publicar_comunicado(
    *,
    autor,
    titulo: str,
    conteudo: str,
    escopo: str,
    papel_destino: str = None,
    curso=None,
    turma=None,
    publicar_em=None,
    expirar_em=None
) -> Comunicado:
    """
    Publica um novo comunicado após validar permissões do publicador e escopo.
    """
    _validar_permissao_publicador(autor, escopo)

    comunicado = Comunicado(
        autor=autor,
        titulo=titulo.strip(),
        conteudo=conteudo.strip(),
        escopo=escopo,
        papel_destino=papel_destino if escopo == EscopoComunicado.PAPEL else None,
        curso=curso if escopo == EscopoComunicado.CURSO else None,
        turma=turma if escopo == EscopoComunicado.TURMA else None,
        publicar_em=publicar_em or timezone.now(),
        expirar_em=expirar_em,
        ativo=True
    )
    comunicado.full_clean()
    comunicado.save()
    return comunicado


@transaction.atomic
def atualizar_comunicado(
    *,
    comunicado: Comunicado,
    autor,
    titulo: str,
    conteudo: str,
    escopo: str,
    papel_destino: str = None,
    curso=None,
    turma=None,
    publicar_em=None,
    expirar_em=None,
    ativo: bool = True
) -> Comunicado:
    """
    Atualiza um comunicado existente.
    """
    _validar_permissao_publicador(autor, escopo)

    if not autor.is_superuser and autor.role not in ('COORDENACAO', 'SECRETARIA'):
        raise PermissionDenied("Sem permissão para editar comunicado.")

    comunicado.titulo = titulo.strip()
    comunicado.conteudo = conteudo.strip()
    comunicado.escopo = escopo
    comunicado.papel_destino = papel_destino if escopo == EscopoComunicado.PAPEL else None
    comunicado.curso = curso if escopo == EscopoComunicado.CURSO else None
    comunicado.turma = turma if escopo == EscopoComunicado.TURMA else None
    if publicar_em:
        comunicado.publicar_em = publicar_em
    comunicado.expirar_em = expirar_em
    comunicado.ativo = ativo

    comunicado.full_clean()
    comunicado.save()
    return comunicado


@transaction.atomic
def inativar_comunicado(*, comunicado: Comunicado, autor) -> None:
    """
    Inativa logicamente um comunicado.
    """
    if not autor.is_superuser and autor.role not in ('COORDENACAO', 'SECRETARIA'):
        raise PermissionDenied("Sem permissão para inativar comunicado.")

    comunicado.ativo = False
    comunicado.save(update_fields=['ativo'])
