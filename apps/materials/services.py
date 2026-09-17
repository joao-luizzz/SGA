from django.core.exceptions import PermissionDenied
from django.db import transaction
from .models import MaterialAcademico


def _validar_permissao_autor(turma, autor):
    """
    Valida se o usuário tem permissão para gerenciar materiais da turma.
    Apenas o professor atribuído à turma ou a coordenação podem gerenciar.
    """
    if autor.role == 'COORDENACAO':
        return True
    if autor.role == 'PROFESSOR' and turma.professor_id == autor.id:
        return True
    raise PermissionDenied("Você não tem permissão para gerenciar materiais desta turma.")


def _remover_arquivo_apos_commit(storage, nome_arquivo):
    if nome_arquivo:
        transaction.on_commit(lambda: storage.delete(nome_arquivo))


@transaction.atomic
def criar_material(*, turma, autor, titulo, descricao="", arquivo=None, link=None) -> MaterialAcademico:
    """
    Cria um novo material acadêmico para a turma.
    """
    _validar_permissao_autor(turma, autor)

    material = MaterialAcademico(
        turma=turma,
        autor=autor,
        titulo=titulo.strip(),
        descricao=descricao.strip(),
        arquivo=arquivo,
        link=link.strip() if link else None,
    )
    material.full_clean()
    material.save()
    return material


@transaction.atomic
def atualizar_material(
    *,
    material: MaterialAcademico,
    autor,
    titulo: str,
    descricao: str = "",
    arquivo=None,
    link: str = None,
) -> MaterialAcademico:
    """
    Atualiza um material acadêmico existente.
    """
    _validar_permissao_autor(material.turma, autor)

    antigo_arquivo_nome = material.arquivo.name
    storage = material.arquivo.storage

    material.titulo = titulo.strip()
    material.descricao = descricao.strip()

    if arquivo:
        material.arquivo = arquivo
        material.link = None
    elif link:
        material.arquivo = None
        material.link = link.strip()

    material.full_clean()
    material.save()
    if material.arquivo.name != antigo_arquivo_nome:
        _remover_arquivo_apos_commit(storage, antigo_arquivo_nome)
    return material


@transaction.atomic
def excluir_material(*, material: MaterialAcademico, autor) -> None:
    """
    Exclui um material acadêmico e agenda a remoção do arquivo após o commit.
    """
    _validar_permissao_autor(material.turma, autor)

    nome_arquivo = material.arquivo.name
    storage = material.arquivo.storage
    material.delete()
    _remover_arquivo_apos_commit(storage, nome_arquivo)
