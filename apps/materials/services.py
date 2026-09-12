import os
from django.core.exceptions import PermissionDenied, ValidationError
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
    remover_arquivo_anterior: bool = False
) -> MaterialAcademico:
    """
    Atualiza um material acadêmico existente.
    """
    _validar_permissao_autor(material.turma, autor)

    antigo_arquivo = material.arquivo

    material.titulo = titulo.strip()
    material.descricao = descricao.strip()

    if arquivo:
        # Se um novo arquivo foi enviado, exclui o anterior se existir
        if antigo_arquivo and antigo_arquivo != arquivo and os.path.isfile(antigo_arquivo.path):
            try:
                os.remove(antigo_arquivo.path)
            except OSError:
                pass
        material.arquivo = arquivo
        material.link = None
    elif link:
        # Se virou link, exclui o arquivo antigo
        if antigo_arquivo and os.path.isfile(antigo_arquivo.path):
            try:
                os.remove(antigo_arquivo.path)
            except OSError:
                pass
        material.arquivo = None
        material.link = link.strip()
    elif remover_arquivo_anterior:
        if antigo_arquivo and os.path.isfile(antigo_arquivo.path):
            try:
                os.remove(antigo_arquivo.path)
            except OSError:
                pass
        material.arquivo = None

    material.full_clean()
    material.save()
    return material


@transaction.atomic
def excluir_material(*, material: MaterialAcademico, autor) -> None:
    """
    Exclui um material acadêmico e apaga o arquivo físico associado.
    """
    _validar_permissao_autor(material.turma, autor)

    if material.arquivo:
        try:
            if os.path.isfile(material.arquivo.path):
                os.remove(material.arquivo.path)
        except OSError:
            pass

    material.delete()
