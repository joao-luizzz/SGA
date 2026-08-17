import pytest
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole

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


@pytest.mark.django_db
class TestTurmaModels:
    @pytest.fixture
    def setup_dados(self):
        curso = Curso.objects.create(nome="Análise e Desenvolvimento de Sistemas", codigo="ADS")
        disciplina = Disciplina.objects.create(nome="Programação Orientada a Objetos", codigo="ADS-POO", carga_horaria=80, curso=curso)
        professor = CustomUser.objects.create_user(
            email='professor_teste@sga.edu.br',
            full_name='Professor Teste',
            password='senha',
            role=UserRole.PROFESSOR
        )
        return {
            'curso': curso,
            'disciplina': disciplina,
            'professor': professor
        }

    def test_criar_turma_sem_professor(self, setup_dados):
        disciplina = setup_dados['disciplina']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40
        )
        assert turma.disciplina == disciplina
        assert turma.periodo_letivo == "2026/1"
        assert turma.horarios == "SEG 19:00-22:30"
        assert turma.vagas_maximas == 40
        assert turma.professor is None
        assert turma.ativo is True
        assert str(turma) == "Programação Orientada a Objetos (2026/1) - Sem professor alocado"

    def test_criar_turma_com_professor(self, setup_dados):
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40,
            professor=professor
        )
        assert turma.professor == professor
        assert str(turma) == "Programação Orientada a Objetos (2026/1) - Professor Teste"

    def test_metodo_pode_receber_matricula(self, setup_dados):
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']
        
        # 1. Sem professor (deve retornar False)
        turma_sem_prof = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40
        )
        assert turma_sem_prof.pode_receber_matricula() is False

        # 2. Com professor e ativa (deve retornar True)
        turma_com_prof = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        assert turma_com_prof.pode_receber_matricula() is True

        # 3. Com professor, mas inativa (deve retornar False)
        turma_com_prof.ativo = False
        turma_com_prof.save()
        assert turma_com_prof.pode_receber_matricula() is False

    def test_inativacao_turma_nao_deleta_registro(self, setup_dados):
        disciplina = setup_dados['disciplina']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40
        )
        turma.ativo = False
        turma.save()

        # Deve continuar no banco
        turma_db = Turma.objects.get(pk=turma.pk)
        assert turma_db is not None
        assert turma_db.ativo is False
        assert str(turma_db) == "Programação Orientada a Objetos (2026/1) - Sem professor alocado (Inativa)"

