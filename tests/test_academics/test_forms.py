import pytest
from academics.models import Curso, Disciplina, Turma
from academics.forms import CursoForm, DisciplinaForm, TurmaForm
from accounts.models import CustomUser, UserRole

@pytest.mark.django_db
class TestAcademicsForms:
    def test_curso_form_valido(self):
        form_data = {
            'nome': 'Ciência da Computação',
            'codigo': 'CC',
            'descricao': 'Bacharelado em Ciência da Computação',
            'ativo': True
        }
        form = CursoForm(data=form_data)
        assert form.is_valid() is True

    def test_curso_form_codigo_duplicado_falha(self):
        # Primeiro, persistimos um curso
        Curso.objects.create(nome='Ciência da Computação', codigo='CC')
        
        # Tentativa de validar formulário com o mesmo código
        form_data = {
            'nome': 'Outro Curso com mesmo Código',
            'codigo': 'cc',  # Caixa baixa deve ser normalizada/comparada de forma case-insensitive
            'descricao': '',
            'ativo': True
        }
        form = CursoForm(data=form_data)
        assert form.is_valid() is False
        assert 'codigo' in form.errors
        assert form.errors['codigo'][0] == "Já existe um curso cadastrado com este código."

    def test_disciplina_form_valido(self):
        curso = Curso.objects.create(nome='Ciência da Computação', codigo='CC')
        form_data = {
            'nome': 'Estruturas de Dados',
            'codigo': 'CC-ED',
            'carga_horaria': 80,
            'curso': curso.pk,
            'ativo': True
        }
        form = DisciplinaForm(data=form_data)
        assert form.is_valid() is True

    def test_disciplina_form_codigo_duplicado_falha(self):
        curso = Curso.objects.create(nome='Ciência da Computação', codigo='CC')
        # Primeiro, persistimos uma disciplina
        Disciplina.objects.create(
            nome='Estruturas de Dados',
            codigo='CC-ED',
            carga_horaria=80,
            curso=curso
        )
        
        # Tentativa de validar formulário de outra disciplina com o mesmo código
        form_data = {
            'nome': 'Algoritmos e Estruturas de Dados',
            'codigo': 'cc-ed',  # Comparação deve cobrir maiúsculo/minúsculo normalizado
            'carga_horaria': 80,
            'curso': curso.pk,
            'ativo': True
        }
        form = DisciplinaForm(data=form_data)
        assert form.is_valid() is False
        assert 'codigo' in form.errors
        assert form.errors['codigo'][0] == "Já existe uma disciplina cadastrada com este código."

    def test_disciplina_form_carga_horaria_invalida(self):
        curso = Curso.objects.create(nome='Ciência da Computação', codigo='CC')
        form_data = {
            'nome': 'Estruturas de Dados',
            'codigo': 'CC-ED',
            'carga_horaria': 0,  # Carga horária zero é inválida
            'curso': curso.pk,
            'ativo': True
        }
        form = DisciplinaForm(data=form_data)
        assert form.is_valid() is False
        assert 'carga_horaria' in form.errors
        assert form.errors['carga_horaria'][0] == "A carga horária deve ser maior que zero."


@pytest.mark.django_db
class TestTurmaForms:
    @pytest.fixture
    def setup_dados(self):
        curso = Curso.objects.create(nome='Ciência da Computação', codigo='CC')
        disciplina = Disciplina.objects.create(nome='Banco de Dados', codigo='CC-BD', carga_horaria=80, curso=curso)
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

    def test_turma_form_valido_sem_professor(self, setup_dados):
        disciplina = setup_dados['disciplina']
        form_data = {
            'disciplina': disciplina.pk,
            'periodo_letivo': '2026/1',
            'horarios': 'SEG 19:00-22:30',
            'sala': 'Sala 101',
            'vagas_maximas': 40,
            'professor': '',  # Professor opcional na criação
            'ativo': True
        }
        form = TurmaForm(data=form_data)
        assert form.is_valid() is True

    def test_turma_form_valido_com_professor(self, setup_dados):
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']
        form_data = {
            'disciplina': disciplina.pk,
            'periodo_letivo': '2026/1',
            'horarios': 'SEG 19:00-22:30',
            'sala': 'Sala 101',
            'vagas_maximas': 40,
            'professor': professor.pk,
            'ativo': True
        }
        form = TurmaForm(data=form_data)
        assert form.is_valid() is True

    def test_turma_form_periodo_letivo_invalido(self, setup_dados):
        disciplina = setup_dados['disciplina']
        form_data = {
            'disciplina': disciplina.pk,
            'periodo_letivo': '2026-1',  # Formato inválido (deve ser AAAA/N)
            'horarios': 'SEG 19:00-22:30',
            'vagas_maximas': 40,
            'ativo': True
        }
        form = TurmaForm(data=form_data)
        assert form.is_valid() is False
        assert 'periodo_letivo' in form.errors
        assert form.errors['periodo_letivo'][0] == "O período letivo deve seguir o formato AAAA/N (ex: 2026/1)."

    def test_turma_form_vagas_maximas_invalidas(self, setup_dados):
        disciplina = setup_dados['disciplina']
        form_data = {
            'disciplina': disciplina.pk,
            'periodo_letivo': '2026/1',
            'horarios': 'SEG 19:00-22:30',
            'vagas_maximas': 0,  # Vagas inválidas (deve ser > 0)
            'ativo': True
        }
        form = TurmaForm(data=form_data)
        assert form.is_valid() is False
        assert 'vagas_maximas' in form.errors
        assert form.errors['vagas_maximas'][0] == "A quantidade de vagas máximas deve ser maior que zero."

