import pytest
from academics.models import Curso, Disciplina

@pytest.mark.django_db
class TestAcademicsModels:
    def test_criar_curso(self):
        curso = Curso.objects.create(
            nome="Análise e Desenvolvimento de Sistemas",
            codigo="ADS",
            descricao="Curso de graduação tecnológica"
        )
        assert curso.nome == "Análise e Desenvolvimento de Sistemas"
        assert curso.codigo == "ADS"
        assert curso.ativo is True
        assert str(curso) == "Análise e Desenvolvimento de Sistemas - ADS"

    def test_criar_disciplina(self):
        curso = Curso.objects.create(
            nome="Análise e Desenvolvimento de Sistemas",
            codigo="ADS"
        )
        disciplina = Disciplina.objects.create(
            nome="Programação Orientada a Objetos",
            codigo="ADS-POO",
            carga_horaria=80,
            curso=curso
        )
        assert disciplina.nome == "Programação Orientada a Objetos"
        assert disciplina.codigo == "ADS-POO"
        assert disciplina.carga_horaria == 80
        assert disciplina.curso == curso
        assert disciplina.ativo is True
        assert str(disciplina) == "Programação Orientada a Objetos - ADS-POO (80h)"

    def test_inativacao_curso_nao_deleta_registro(self):
        curso = Curso.objects.create(
            nome="Sistemas de Informação",
            codigo="SI"
        )
        # Inativar curso
        curso.ativo = False
        curso.save()
        
        # Recarregar do banco de dados
        curso_db = Curso.objects.get(pk=curso.pk)
        assert curso_db is not None
        assert curso_db.ativo is False
        assert str(curso_db) == "Sistemas de Informação - SI (Inativo)"

    def test_inativacao_disciplina_nao_deleta_registro(self):
        curso = Curso.objects.create(
            nome="Sistemas de Informação",
            codigo="SI"
        )
        disciplina = Disciplina.objects.create(
            nome="Engenharia de Software",
            codigo="SI-ES",
            carga_horaria=60,
            curso=curso
        )
        # Inativar disciplina
        disciplina.ativo = False
        disciplina.save()
        
        # Recarregar do banco de dados
        disciplina_db = Disciplina.objects.get(pk=disciplina.pk)
        assert disciplina_db is not None
        assert disciplina_db.ativo is False
        assert str(disciplina_db) == "Engenharia de Software - SI-ES (60h) (Inativa)"
