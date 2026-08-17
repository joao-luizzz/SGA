import pytest
from django.urls import reverse
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole

@pytest.mark.django_db
class TestAcademicsViewsRBAC:
    # 1. Bloqueio de acesso para perfis não autorizados (RBAC)
    @pytest.mark.parametrize('role_fixture', ['user_aluno', 'user_professor', 'user_secretaria'])
    def test_perfis_nao_autorizados_bloqueados_na_index(self, client, request, role_fixture, password):
        user = request.getfixturevalue(role_fixture)
        client.login(username=user.email, password=password)
        
        url = reverse('academics:index')
        response = client.get(url)
        assert response.status_code == 403

    @pytest.mark.parametrize('role_fixture', ['user_aluno', 'user_professor', 'user_secretaria'])
    def test_perfis_nao_autorizados_bloqueados_no_curso_create(self, client, request, role_fixture, password):
        user = request.getfixturevalue(role_fixture)
        client.login(username=user.email, password=password)
        
        url = reverse('academics:curso_create')
        response = client.get(url)
        assert response.status_code == 403

    @pytest.mark.parametrize('role_fixture', ['user_aluno', 'user_professor', 'user_secretaria'])
    def test_perfis_nao_autorizados_bloqueados_no_curso_inactivate(self, client, request, role_fixture, password):
        user = request.getfixturevalue(role_fixture)
        client.login(username=user.email, password=password)
        
        curso = Curso.objects.create(nome="Curso Teste", codigo="CT")
        url = reverse('academics:curso_inactivate', args=[curso.pk])
        response = client.post(url)
        assert response.status_code == 403

    # 2. Permissão de acesso garantida para COORDENACAO
    def test_coordenacao_acessa_index(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        url = reverse('academics:index')
        response = client.get(url)
        assert response.status_code == 200
        assert "Catálogo Acadêmico".encode() in response.content

    def test_coordenacao_acessa_curso_create(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        url = reverse('academics:curso_create')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAcademicsViewsFlow:
    # 3. Teste de Fluxo de Criação, Edição e Inativação
    def test_coordenacao_cria_curso_com_sucesso(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        url = reverse('academics:curso_create')
        
        data = {
            'nome': 'Engenharia Elétrica',
            'codigo': 'EE',
            'descricao': 'Curso de Engenharia Elétrica',
            'ativo': True
        }
        response = client.post(url, data)
        # Deve redirecionar para a listagem
        assert response.status_code == 302
        assert response.url == reverse('academics:index')
        
        # Deve ter persistido no banco
        assert Curso.objects.filter(codigo='EE').exists()
        curso = Curso.objects.get(codigo='EE')
        assert curso.nome == 'Engenharia Elétrica'

    def test_coordenacao_edita_curso_com_sucesso(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        curso = Curso.objects.create(nome='Engenharia Elétrica', codigo='EE')
        
        url = reverse('academics:curso_update', args=[curso.pk])
        data = {
            'nome': 'Engenharia Elétrica Renovada',
            'codigo': 'EER',  # Mudança de código
            'descricao': 'Descrição Nova',
            'ativo': True
        }
        response = client.post(url, data)
        assert response.status_code == 302
        
        # Verifica alterações no banco
        curso_atualizado = Curso.objects.get(pk=curso.pk)
        assert curso_atualizado.nome == 'Engenharia Elétrica Renovada'
        assert curso_atualizado.codigo == 'EER'

    def test_coordenacao_inativa_curso_com_sucesso(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        curso = Curso.objects.create(nome='Engenharia Elétrica', codigo='EE', ativo=True)
        
        url = reverse('academics:curso_inactivate', args=[curso.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('academics:index')
        
        # Curso deve continuar no banco de dados, mas inativo
        curso_db = Curso.objects.get(pk=curso.pk)
        assert curso_db is not None
        assert curso_db.ativo is False

    def test_coordenacao_cria_disciplina_com_sucesso(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        curso = Curso.objects.create(nome='Sistemas', codigo='SIS')
        
        url = reverse('academics:disciplina_create')
        data = {
            'nome': 'Banco de Dados',
            'codigo': 'SIS-BD',
            'carga_horaria': 80,
            'curso': curso.pk,
            'ativo': True
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse('academics:index')
        
        assert Disciplina.objects.filter(codigo='SIS-BD').exists()
        disciplina = Disciplina.objects.get(codigo='SIS-BD')
        assert disciplina.nome == 'Banco de Dados'
        assert disciplina.carga_horaria == 80

    def test_coordenacao_inativa_disciplina_com_sucesso(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        curso = Curso.objects.create(nome='Sistemas', codigo='SIS')
        disciplina = Disciplina.objects.create(
            nome='Banco de Dados',
            codigo='SIS-BD',
            carga_horaria=80,
            curso=curso,
            ativo=True
        )
        
        url = reverse('academics:disciplina_inactivate', args=[disciplina.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('academics:index')
        
        # Disciplina deve continuar no banco de dados, mas inativa
        disciplina_db = Disciplina.objects.get(pk=disciplina.pk)
        assert disciplina_db is not None
        assert disciplina_db.ativo is False


@pytest.mark.django_db
class TestTurmaViews:
    @pytest.fixture
    def setup_dados(self):
        curso = Curso.objects.create(nome='Ciência da Computação', codigo='CC')
        disciplina = Disciplina.objects.create(nome='Sistemas Operacionais', codigo='CC-SO', carga_horaria=80, curso=curso)
        professor = CustomUser.objects.create_user(
            email='prof_view@sga.edu.br',
            full_name='Prof View',
            password='senha',
            role=UserRole.PROFESSOR
        )
        return {
            'curso': curso,
            'disciplina': disciplina,
            'professor': professor
        }

    def test_coordenacao_acessa_index_com_turmas(self, client, user_coordenacao, password, setup_dados):
        client.login(username=user_coordenacao.email, password=password)
        disciplina = setup_dados['disciplina']
        Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='SEG 19:00-22:30',
            vagas_maximas=40
        )
        url = reverse('academics:index')
        response = client.get(url)
        assert response.status_code == 200
        assert "Turmas Oferecidas".encode() in response.content

    def test_coordenacao_acessa_turma_create(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        url = reverse('academics:turma_create')
        response = client.get(url)
        assert response.status_code == 200
        assert "Abrir Nova Turma".encode() in response.content

    def test_coordenacao_cria_turma_com_sucesso(self, client, user_coordenacao, password, setup_dados):
        client.login(username=user_coordenacao.email, password=password)
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']
        url = reverse('academics:turma_create')
        form_data = {
            'disciplina': disciplina.pk,
            'periodo_letivo': '2026/1',
            'horarios': 'TER 19:00-22:30',
            'sala': 'Laboratório 202',
            'vagas_maximas': 35,
            'professor': professor.pk,
            'ativo': True
        }
        response = client.post(url, form_data)
        assert response.status_code == 302
        assert response.url == reverse('academics:index')
        assert Turma.objects.filter(periodo_letivo='2026/1', sala='Laboratório 202').exists() is True

    def test_coordenacao_edita_turma_com_sucesso(self, client, user_coordenacao, password, setup_dados):
        client.login(username=user_coordenacao.email, password=password)
        disciplina = setup_dados['disciplina']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='SEG 19:00-22:30',
            vagas_maximas=40
        )
        url = reverse('academics:turma_update', args=[turma.pk])
        form_data = {
            'disciplina': disciplina.pk,
            'periodo_letivo': '2026/2',
            'horarios': 'SEG 19:00-22:30',
            'sala': 'Sala Virtual',
            'vagas_maximas': 45,
            'professor': '',
            'ativo': True
        }
        response = client.post(url, form_data)
        assert response.status_code == 302
        assert response.url == reverse('academics:index')
        
        turma_db = Turma.objects.get(pk=turma.pk)
        assert turma_db.periodo_letivo == '2026/2'
        assert turma_db.sala == 'Sala Virtual'
        assert turma_db.vagas_maximas == 45

    def test_coordenacao_inativa_turma_com_sucesso(self, client, user_coordenacao, password, setup_dados):
        client.login(username=user_coordenacao.email, password=password)
        disciplina = setup_dados['disciplina']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='SEG 19:00-22:30',
            vagas_maximas=40
        )
        url = reverse('academics:turma_inactivate', args=[turma.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('academics:index')
        
        turma_db = Turma.objects.get(pk=turma.pk)
        assert turma_db.ativo is False

    @pytest.mark.parametrize('role', [UserRole.ALUNO, UserRole.PROFESSOR, UserRole.SECRETARIA])
    def test_perfis_nao_autorizados_recebem_403_em_views_de_turma(self, client, db, password, setup_dados, role):
        # Criar usuário com o perfil parametrizado
        user = CustomUser.objects.create_user(
            email=f'user_{role.lower()}@sga.edu.br',
            full_name='Usuário de Teste',
            password=password,
            role=role
        )
        client.login(username=user.email, password=password)
        disciplina = setup_dados['disciplina']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='SEG 19:00-22:30',
            vagas_maximas=40
        )

        urls = [
            reverse('academics:turma_create'),
            reverse('academics:turma_update', args=[turma.pk]),
            reverse('academics:turma_inactivate', args=[turma.pk]),
        ]

        for url in urls:
            if url == reverse('academics:turma_inactivate', args=[turma.pk]):
                response = client.post(url)
            else:
                response = client.get(url)
            assert response.status_code == 403

