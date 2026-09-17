import os
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError
from django.core.files.uploadedfile import SimpleUploadedFile
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from materials.models import MaterialAcademico
from materials.services import criar_material, atualizar_material, excluir_material


@pytest.mark.django_db
class TestMaterialServices:
    @pytest.fixture
    def setup_ambiente(self, user_professor, user_aluno, user_coordenacao):
        curso = Curso.objects.create(codigo="DIR", nome="Direito")
        disciplina = Disciplina.objects.create(codigo="DIR101", nome="Direito Civil", curso=curso, carga_horaria=60)
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026.1",
            horarios="TER 19:00-21:00",
            vagas_maximas=50,
            professor=user_professor
        )
        outro_professor = CustomUser.objects.create_user(
            email="outro_prof@sga.edu.br",
            full_name="Outro Professor",
            role=UserRole.PROFESSOR,
            password="Senha123!teste"
        )
        return turma, user_professor, outro_professor, user_aluno, user_coordenacao

    def test_professor_da_turma_cria_material_com_sucesso(self, setup_ambiente):
        turma, prof, _, _, _ = setup_ambiente
        material = criar_material(
            turma=turma,
            autor=prof,
            titulo="Ementa do Curso",
            descricao="Leia atentamente",
            link="https://universidade.edu.br/ementa"
        )
        assert material.pk is not None
        assert material.titulo == "Ementa do Curso"

    def test_coordenacao_cria_material_com_sucesso(self, setup_ambiente):
        turma, _, _, _, coord = setup_ambiente
        material = criar_material(
            turma=turma,
            autor=coord,
            titulo="Aviso Coordenação",
            link="https://coord.edu.br"
        )
        assert material.pk is not None

    def test_aluno_nao_pode_criar_material(self, setup_ambiente):
        turma, _, _, aluno, _ = setup_ambiente
        with pytest.raises(PermissionDenied):
            criar_material(
                turma=turma,
                autor=aluno,
                titulo="Tentativa de Aluno",
                link="https://aluno.com"
            )

    def test_outro_professor_nao_pode_criar_material_em_turma_alheia(self, setup_ambiente):
        turma, _, outro_prof, _, _ = setup_ambiente
        with pytest.raises(PermissionDenied):
            criar_material(
                turma=turma,
                autor=outro_prof,
                titulo="Material Invasivo",
                link="https://outro.com"
            )

    def test_atualizar_material_substituindo_arquivo_por_link(self, setup_ambiente, django_capture_on_commit_callbacks):
        turma, prof, _, _, _ = setup_ambiente
        arquivo = SimpleUploadedFile("apostila_antiga.pdf", b"dados", content_type="application/pdf")
        material = criar_material(
            turma=turma,
            autor=prof,
            titulo="Apostila",
            arquivo=arquivo
        )
        caminho_antigo = material.arquivo.path
        assert os.path.exists(caminho_antigo)

        with django_capture_on_commit_callbacks(execute=True):
            atualizar_material(
                material=material,
                autor=prof,
                titulo="Novo Link de Apostila",
                link="https://livro.com/apostila"
            )
        material.refresh_from_db()
        assert material.titulo == "Novo Link de Apostila"
        assert material.is_link is True
        assert not os.path.exists(caminho_antigo)

    def test_atualizar_material_substituindo_arquivo_por_novo_arquivo(self, setup_ambiente, django_capture_on_commit_callbacks):
        turma, prof, _, _, _ = setup_ambiente
        arquivo1 = SimpleUploadedFile("v1.pdf", b"versao 1", content_type="application/pdf")
        material = criar_material(turma=turma, autor=prof, titulo="Doc V1", arquivo=arquivo1)
        caminho1 = material.arquivo.path

        arquivo2 = SimpleUploadedFile("v2.pdf", b"versao 2", content_type="application/pdf")
        with django_capture_on_commit_callbacks(execute=True):
            atualizar_material(material=material, autor=prof, titulo="Doc V2", arquivo=arquivo2)
        material.refresh_from_db()
        assert material.titulo == "Doc V2"
        assert not os.path.exists(caminho1)
        assert os.path.exists(material.arquivo.path)

    def test_excluir_material_apaga_arquivo_do_disco(self, setup_ambiente, django_capture_on_commit_callbacks):
        turma, prof, _, _, _ = setup_ambiente
        arquivo = SimpleUploadedFile("apostila.pdf", b"conteudo apostila teste", content_type="application/pdf")
        material = criar_material(
            turma=turma,
            autor=prof,
            titulo="Apostila",
            arquivo=arquivo
        )
        caminho_arquivo = material.arquivo.path
        assert os.path.exists(caminho_arquivo)

        with django_capture_on_commit_callbacks(execute=True):
            excluir_material(material=material, autor=prof)
        assert not MaterialAcademico.objects.filter(pk=material.pk).exists()
        assert not os.path.exists(caminho_arquivo)

    def test_falha_na_validacao_preserva_arquivo_anterior(self, setup_ambiente):
        turma, prof, _, _, _ = setup_ambiente
        material = criar_material(
            turma=turma,
            autor=prof,
            titulo="Apostila",
            arquivo=SimpleUploadedFile("apostila.pdf", b"dados"),
        )
        caminho_antigo = material.arquivo.path

        with pytest.raises(ValidationError):
            atualizar_material(
                material=material,
                autor=prof,
                titulo="Apostila atualizada",
                arquivo=SimpleUploadedFile("invalido.exe", b"dados"),
            )

        material.refresh_from_db()
        assert material.arquivo.path == caminho_antigo
        assert os.path.exists(caminho_antigo)

    def test_falha_no_salvamento_preserva_arquivo_anterior(self, setup_ambiente, monkeypatch):
        turma, prof, _, _, _ = setup_ambiente
        material = criar_material(
            turma=turma,
            autor=prof,
            titulo="Apostila",
            arquivo=SimpleUploadedFile("apostila.pdf", b"dados"),
        )
        caminho_antigo = material.arquivo.path

        def falhar_salvamento(*args, **kwargs):
            raise DatabaseError("falha de banco simulada")

        monkeypatch.setattr(MaterialAcademico, "save", falhar_salvamento)

        with pytest.raises(DatabaseError):
            atualizar_material(
                material=material,
                autor=prof,
                titulo="Apostila atualizada",
                arquivo=SimpleUploadedFile("nova.pdf", b"dados"),
            )

        assert os.path.exists(caminho_antigo)
