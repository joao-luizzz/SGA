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
            sala="Sala 101",
            vagas_maximas=40
        )
        assert turma_sem_prof.pode_receber_matricula() is False

        # 2. Com professor, sala, horário, vagas > 0 e ativa (deve retornar True)
        turma_com_tudo = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        assert turma_com_tudo.pode_receber_matricula() is True

        # 3. Com professor, mas inativa (deve retornar False)
        turma_com_tudo.ativo = False
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False
        turma_com_tudo.ativo = True
        turma_com_tudo.save()

        # 4. Sem sala (deve retornar False)
        turma_com_tudo.sala = ""
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False
        turma_com_tudo.sala = "Sala 101"
        turma_com_tudo.save()

        # 5. Sem horário (deve retornar False)
        turma_com_tudo.horarios = ""
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False
        turma_com_tudo.horarios = "SEG 19:00-22:30"
        turma_com_tudo.save()

        # 6. Vagas inválidas (<= 0) (deve retornar False)
        turma_com_tudo.vagas_maximas = 0
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False

    def test_conflito_horario_professor(self, setup_dados):
        from django.core.exceptions import ValidationError
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']

        # Criar outro professor de teste
        outro_professor = CustomUser.objects.create_user(
            email='outro_prof@sga.edu.br',
            full_name='Outro Professor',
            password='senha',
            role=UserRole.PROFESSOR
        )

        # Turma base ativa para o Professor (SEG 19:00-20:40)
        turma_base = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-20:40",
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        # Executa clean() da turma_base (deve passar sem problemas)
        turma_base.clean()

        # 1. PERMITIR turmas com professores diferentes no mesmo horário/período
        turma_outro_prof = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-20:40",  # Horário idêntico
            sala="Sala 102",
            vagas_maximas=40,
            professor=outro_professor,
            ativo=True
        )
        turma_outro_prof.clean()  # Não deve levantar erro

        # 2. PERMITIR o mesmo professor em dias diferentes
        turma_outro_dia = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="TER 19:00-20:40",  # Horário igual, mas em dia diferente (TER)
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        turma_outro_dia.clean()  # Não deve levantar erro

        # 3. PERMITIR o mesmo professor em horários adjacentes (ex: Turma base termina 20:40, nova inicia 20:40)
        turma_adjacente = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 20:40-22:20",  # Adjacente
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        turma_adjacente.clean()  # Não deve levantar erro

        # 4. BLOQUEAR o mesmo professor em horários com sobreposição real parcial (ex: SEG 20:00-21:40 conflitante)
        turma_sobreposta_parcial = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 20:00-21:40",  # Conflita das 20:00 às 20:40
            sala="Sala 103",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        with pytest.raises(ValidationError) as excinfo:
            turma_sobreposta_parcial.clean()
        assert 'horarios' in excinfo.value.message_dict
        assert "horário conflitante" in excinfo.value.message_dict['horarios'][0]

        # 5. BLOQUEAR o mesmo professor em horários idênticos
        turma_identica = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-20:40",  # Horário idêntico
            sala="Sala 104",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        with pytest.raises(ValidationError) as excinfo:
            turma_identica.clean()
        assert 'horarios' in excinfo.value.message_dict
        assert "horário conflitante" in excinfo.value.message_dict['horarios'][0]


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
