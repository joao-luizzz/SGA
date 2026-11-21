import pytest
from django.urls import reverse
from academics.models import Curso, Disciplina, HorarioTurma, Turma
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
        turma = Turma.objects.get(periodo_letivo='2026/1', sala='Laboratório 202')
        assert turma.horarios_aula.filter(dia_semana='TER').exists()

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
        assert turma_db.horarios_aula.filter(dia_semana='SEG').exists()

    def test_criacao_com_conflito_reverte_turma_e_horarios(
        self, client, user_coordenacao, password, setup_dados
    ):
        client.login(username=user_coordenacao.email, password=password)
        disciplina = setup_dados['disciplina']
        Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='TER 19:00-20:40',
            sala='Sala 101',
            vagas_maximas=40,
        )
        turma_existente = Turma.objects.latest('pk')
        HorarioTurma.objects.create(
            turma=turma_existente,
            dia_semana='TER',
            hora_inicio='19:00',
            hora_fim='20:40',
        )

        response = client.post(
            reverse('academics:turma_create'),
            {
                'disciplina': disciplina.pk,
                'periodo_letivo': '2026/1',
                'horarios': 'TER 20:00-21:00',
                'sala': 'Sala 101',
                'vagas_maximas': 35,
                'professor': '',
                'ativo': True,
            },
        )

        assert response.status_code == 200
        assert response.context['form'].non_field_errors()
        assert Turma.objects.count() == 1
        assert HorarioTurma.objects.count() == 1
        assert HorarioTurma.objects.filter(
            turma=turma_existente,
            dia_semana='TER',
            hora_inicio='19:00',
            hora_fim='20:40',
        ).exists()

    def test_edicao_com_conflito_reverte_turma_e_horarios(
        self, client, user_coordenacao, password, setup_dados
    ):
        client.login(username=user_coordenacao.email, password=password)
        disciplina = setup_dados['disciplina']
        turma_existente = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='TER 19:00-20:40',
            sala='Sala 101',
            vagas_maximas=40,
        )
        HorarioTurma.objects.create(
            turma=turma_existente,
            dia_semana='TER',
            hora_inicio='19:00',
            hora_fim='20:40',
        )
        turma_editada = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='SEG 19:00-20:40',
            sala='Sala 202',
            vagas_maximas=30,
        )
        horario_original = HorarioTurma.objects.create(
            turma=turma_editada,
            dia_semana='SEG',
            hora_inicio='19:00',
            hora_fim='20:40',
        )

        response = client.post(
            reverse('academics:turma_update', args=[turma_editada.pk]),
            {
                'disciplina': disciplina.pk,
                'periodo_letivo': '2026/1',
                'horarios': 'TER 20:00-21:00',
                'sala': 'Sala 101',
                'vagas_maximas': 45,
                'professor': '',
                'ativo': True,
            },
        )

        assert response.status_code == 200
        assert response.context['form'].non_field_errors()
        turma_editada.refresh_from_db()
        assert turma_editada.horarios == 'SEG 19:00-20:40'
        assert turma_editada.sala == 'Sala 202'
        assert turma_editada.vagas_maximas == 30
        assert HorarioTurma.objects.filter(pk=horario_original.pk).exists()
        assert not HorarioTurma.objects.filter(
            turma=turma_editada,
            dia_semana='TER',
        ).exists()

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


@pytest.mark.django_db
class TestHorarioTurmaViews:
    @pytest.fixture
    def setup_dados_views(self):
        curso = Curso.objects.create(nome="Analise de Sistemas", codigo="ADS")
        disc = Disciplina.objects.create(nome="POO", codigo="ADS-POO", carga_horaria=80, curso=curso)
        turma = Turma.objects.create(
            disciplina=disc,
            periodo_letivo="2026/1",
            vagas_maximas=40,
            sala="Sala 101",
            ativo=True
        )
        return {
            'curso': curso,
            'disciplina': disc,
            'turma': turma
        }

    @pytest.mark.parametrize('role', [UserRole.ALUNO, UserRole.PROFESSOR, UserRole.SECRETARIA])
    def test_perfis_nao_autorizados_bloqueados_em_views_de_horario(self, client, password, setup_dados_views, role):
        user = CustomUser.objects.create_user(
            email=f'user_{role.lower()}_horarios@sga.edu.br',
            full_name='Usuário de Teste',
            password=password,
            role=role
        )
        client.login(username=user.email, password=password)
        turma = setup_dados_views['turma']
        
        url_manage = reverse('academics:turma_horarios', args=[turma.pk])
        response = client.get(url_manage)
        assert response.status_code == 403

        from academics.models import HorarioTurma
        from datetime import time
        horario = HorarioTurma.objects.create(
            turma=turma,
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        url_delete = reverse('academics:horario_delete', args=[horario.pk])
        response = client.post(url_delete)
        assert response.status_code == 403

    def test_coordenacao_acessa_turma_horarios(self, client, user_coordenacao, password, setup_dados_views):
        client.login(username=user_coordenacao.email, password=password)
        turma = setup_dados_views['turma']
        url = reverse('academics:turma_horarios', args=[turma.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert "Gerenciar Grade Horária".encode() in response.content
        assert turma.disciplina.nome.encode() in response.content

    def test_coordenacao_cadastra_horario_com_sucesso(self, client, user_coordenacao, password, setup_dados_views):
        client.login(username=user_coordenacao.email, password=password)
        turma = setup_dados_views['turma']
        url = reverse('academics:turma_horarios', args=[turma.pk])
        
        data = {
            'turma': turma.pk,
            'dia_semana': 'TER',
            'hora_inicio': '19:00',
            'hora_fim': '20:40',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse('academics:turma_horarios', args=[turma.pk])
        
        from academics.models import HorarioTurma
        assert HorarioTurma.objects.filter(turma=turma, dia_semana='TER').exists()

    def test_coordenacao_cadastra_horario_com_conflito(self, client, user_coordenacao, password, setup_dados_views):
        client.login(username=user_coordenacao.email, password=password)
        turma = setup_dados_views['turma']
        url = reverse('academics:turma_horarios', args=[turma.pk])
        
        from academics.models import HorarioTurma
        from datetime import time
        HorarioTurma.objects.create(
            turma=turma,
            dia_semana='TER',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )

        data = {
            'turma': turma.pk,
            'dia_semana': 'TER',
            'hora_inicio': '20:00',
            'hora_fim': '21:00',
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert not response.context['form'].is_valid()
        assert len(response.context['form'].errors) > 0
        
        from django.contrib.messages import get_messages
        messages = list(get_messages(response.wsgi_request))
        assert any("Por favor, corrija os erros no formulário abaixo" in str(m) for m in messages)

    def test_coordenacao_deleta_horario_com_sucesso(self, client, user_coordenacao, password, setup_dados_views):
        client.login(username=user_coordenacao.email, password=password)
        turma = setup_dados_views['turma']
        
        from academics.models import HorarioTurma
        from datetime import time
        horario = HorarioTurma.objects.create(
            turma=turma,
            dia_semana='TER',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )

        url = reverse('academics:horario_delete', args=[horario.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse('academics:turma_horarios', args=[turma.pk])
        assert not HorarioTurma.objects.filter(pk=horario.pk).exists()


    def test_aluno_acessa_sua_grade_com_sucesso(self, client, user_aluno, password, setup_dados_views):
        client.login(username=user_aluno.email, password=password)
        
        from academics.models import HorarioTurma
        from datetime import time
        turma = setup_dados_views['turma']
        
        # Matricula o aluno ativamente na turma
        from enrollment.models import Matricula
        Matricula.objects.create(
            aluno=user_aluno,
            turma=turma,
            status='ATIVA'
        )
        
        horario = HorarioTurma.objects.create(
            turma=turma,
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        
        url = reverse('academics:grade_horaria')
        response = client.get(url)
        assert response.status_code == 200
        assert "Minha Grade Horária".encode() in response.content
        assert turma.disciplina.nome.encode() in response.content

    def test_professor_acessa_sua_grade_com_sucesso(self, client, user_professor, password, setup_dados_views):
        client.login(username=user_professor.email, password=password)
        
        from academics.models import HorarioTurma
        from datetime import time
        turma = setup_dados_views['turma']
        turma.professor = user_professor
        turma.save()
        
        horario = HorarioTurma.objects.create(
            turma=turma,
            dia_semana='QUA',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        
        url = reverse('academics:grade_horaria')
        response = client.get(url)
        assert response.status_code == 200
        assert "Minha Grade Horária".encode() in response.content
        assert turma.disciplina.nome.encode() in response.content

    def test_coordenacao_acessa_grade_com_filtros(self, client, user_coordenacao, password, setup_dados_views):
        client.login(username=user_coordenacao.email, password=password)
        
        from academics.models import HorarioTurma
        from datetime import time
        turma = setup_dados_views['turma']
        
        horario = HorarioTurma.objects.create(
            turma=turma,
            dia_semana='QUI',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        
        url = reverse('academics:grade_horaria')
        
        # Acesso padrão
        response = client.get(url)
        assert response.status_code == 200
        assert "Grade Horária Geral".encode() in response.content
        assert turma.disciplina.nome.encode() in response.content
        
        # Acesso filtrando por curso correto
        response = client.get(url, {'curso': turma.disciplina.curso.pk})
        assert response.status_code == 200
        assert turma.disciplina.nome.encode() in response.content
        
        # Acesso filtrando por outro curso inexistente/vazio
        response = client.get(url, {'curso': 99999})
        assert response.status_code == 200
        assert turma.disciplina.nome.encode() not in response.content


