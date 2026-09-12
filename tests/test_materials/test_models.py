import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from materials.models import MaterialAcademico


@pytest.mark.django_db
class TestMaterialAcademicoModel:
    @pytest.fixture
    def setup_turma(self, user_professor):
        curso = Curso.objects.create(codigo="ENG", nome="Engenharia")
        disciplina = Disciplina.objects.create(codigo="ENG101", nome="Cálculo I", curso=curso, carga_horaria=60)
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026.1",
            horarios="SEG 08:00-10:00",
            vagas_maximas=40,
            professor=user_professor
        )
        return turma

    def test_criar_material_com_link_valido(self, setup_turma, user_professor):
        material = MaterialAcademico(
            turma=setup_turma,
            autor=user_professor,
            titulo="Link de Apoio",
            descricao="Vídeo explicativo",
            link="https://www.youtube.com/watch?v=12345"
        )
        material.full_clean()
        material.save()
        assert material.pk is not None
        assert material.is_link is True
        assert material.filename == ""

    def test_criar_material_com_arquivo_valido(self, setup_turma, user_professor):
        arquivo = SimpleUploadedFile("aula1.pdf", b"conteudo do pdf de teste", content_type="application/pdf")
        material = MaterialAcademico(
            turma=setup_turma,
            autor=user_professor,
            titulo="Slides Aula 1",
            arquivo=arquivo
        )
        material.full_clean()
        material.save()
        assert material.pk is not None
        assert material.is_link is False
        assert material.filename.endswith(".pdf")
        assert "aula1" in material.filename

    def test_erro_sem_arquivo_e_sem_link(self, setup_turma, user_professor):
        material = MaterialAcademico(
            turma=setup_turma,
            autor=user_professor,
            titulo="Material Vazio"
        )
        with pytest.raises(ValidationError) as exc:
            material.full_clean()
        assert "É necessário fornecer um arquivo OU um link" in str(exc.value)

    def test_erro_com_arquivo_e_link_simultaneos(self, setup_turma, user_professor):
        arquivo = SimpleUploadedFile("aula.pdf", b"dados", content_type="application/pdf")
        material = MaterialAcademico(
            turma=setup_turma,
            autor=user_professor,
            titulo="Ambos",
            arquivo=arquivo,
            link="https://link.com"
        )
        with pytest.raises(ValidationError) as exc:
            material.full_clean()
        assert "não ambos" in str(exc.value)

    def test_erro_extensao_arquivo_invalida(self, setup_turma, user_professor):
        arquivo = SimpleUploadedFile("malware.exe", b"binario executavel", content_type="application/x-msdownload")
        material = MaterialAcademico(
            turma=setup_turma,
            autor=user_professor,
            titulo="Executável",
            arquivo=arquivo
        )
        with pytest.raises(ValidationError) as exc:
            material.full_clean()
        assert "não permitido" in str(exc.value)
