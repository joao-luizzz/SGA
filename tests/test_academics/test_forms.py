import pytest
from academics.models import Curso, Disciplina
from academics.forms import CursoForm, DisciplinaForm

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
