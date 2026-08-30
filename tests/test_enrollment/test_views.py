import pytest
from django.urls import reverse
from academics.models import Curso, Disciplina, Turma
from enrollment.models import Matricula, StatusMatricula


@pytest.fixture
def curso(db):
    return Curso.objects.create(nome='ADS', codigo='ADS001', ativo=True)


@pytest.fixture
def disciplina(db, curso):
    return Disciplina.objects.create(
        nome='Arquitetura de Software',
        codigo='AS001',
        carga_horaria=60,
        curso=curso,
        ativo=True,
    )


@pytest.fixture
def turma(db, disciplina, user_professor):
    return Turma.objects.create(
        disciplina=disciplina,
        periodo_letivo='2026/1',
        horarios='SEX 08:00-10:00',
        sala='Sala 303',
        vagas_maximas=30,
        professor=user_professor,
        ativo=True,
    )


@pytest.mark.django_db
class TestEnrollmentViews:

    def test_aluno_acessa_minhas_matriculas(self, client, user_aluno, turma, password):
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        client.login(username=user_aluno.email, password=password)
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 200
        assert turma.disciplina.nome.encode() in response.content

    def test_secretaria_acessa_gestao_matriculas(self, client, user_secretaria, password):
        client.login(username=user_secretaria.email, password=password)
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 200
        assert b'Gest\xc3\xa3o de Matr\xc3\xadculas' in response.content

    def test_listagem_administrativa_exibe_dados_da_matricula(
        self, client, user_secretaria, user_aluno, turma
    ):
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        client.force_login(user_secretaria)

        response = client.get(reverse('enrollment:index'))

        assert response.status_code == 200
        assert user_aluno.full_name.encode() in response.content
        assert turma.disciplina.nome.encode() in response.content
        assert turma.periodo_letivo.encode() in response.content
        assert b'Ativa' in response.content
        assert reverse('enrollment:matricula_create').encode() in response.content

    def test_professor_bloqueado_em_matriculas(self, client, user_professor, password):
        client.login(username=user_professor.email, password=password)
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 403

    def test_anonimo_redirecionado_login(self, client):
        url = reverse('enrollment:index')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/' in response['Location']

    @pytest.mark.parametrize('usuario_fixture', ['user_aluno', 'user_professor'])
    def test_apenas_secretaria_acessa_matricula_administrativa(
        self, client, request, usuario_fixture
    ):
        client.force_login(request.getfixturevalue(usuario_fixture))

        response = client.get(reverse('enrollment:matricula_create'))

        assert response.status_code == 403

    @pytest.mark.parametrize(
        'usuario_fixture', ['user_aluno', 'user_professor', 'user_coordenacao']
    )
    def test_apenas_secretaria_acessa_rotas_administrativas_de_matricula(
        self, client, request, usuario_fixture, user_aluno, turma
    ):
        matricula = Matricula.objects.create(aluno=user_aluno, turma=turma)
        client.force_login(request.getfixturevalue(usuario_fixture))

        assert client.get(reverse('enrollment:matricula_create')).status_code == 403
        assert client.post(
            reverse('enrollment:matricula_status', args=[matricula.pk]),
            data={'status': StatusMatricula.TRANCADA},
        ).status_code == 403

    def test_secretaria_matricula_aluno_com_sucesso(
        self, client, user_secretaria, user_aluno, turma
    ):
        client.force_login(user_secretaria)

        response = client.post(
            reverse('enrollment:matricula_create'),
            data={'aluno': user_aluno.pk, 'turma': turma.pk},
        )

        assert response.status_code == 302
        assert Matricula.objects.filter(
            aluno=user_aluno,
            turma=turma,
            status=StatusMatricula.ATIVA,
        ).exists()

    @pytest.mark.parametrize(
        'novo_status',
        [StatusMatricula.TRANCADA, StatusMatricula.CANCELADA, StatusMatricula.CONCLUIDA],
    )
    def test_secretaria_altera_status_de_matricula_ativa(
        self, client, user_secretaria, user_aluno, turma, novo_status
    ):
        matricula = Matricula.objects.create(aluno=user_aluno, turma=turma)
        client.force_login(user_secretaria)

        response = client.post(
            reverse('enrollment:matricula_status', args=[matricula.pk]),
            data={'status': novo_status},
        )

        assert response.status_code == 302
        matricula.refresh_from_db()
        assert matricula.status == novo_status

    @pytest.mark.parametrize(
        'status_final',
        [StatusMatricula.TRANCADA, StatusMatricula.CANCELADA, StatusMatricula.CONCLUIDA],
    )
    def test_secretaria_nao_altera_novamente_matricula_encerrada(
        self, client, user_secretaria, user_aluno, turma, status_final
    ):
        matricula = Matricula.objects.create(
            aluno=user_aluno, turma=turma, status=status_final
        )
        client.force_login(user_secretaria)

        response = client.post(
            reverse('enrollment:matricula_status', args=[matricula.pk]),
            data={'status': StatusMatricula.ATIVA},
            follow=True,
        )

        assert response.status_code == 200
        matricula.refresh_from_db()
        assert matricula.status == status_final

    @pytest.mark.parametrize(
        'status_final', [StatusMatricula.TRANCADA, StatusMatricula.CANCELADA]
    )
    def test_secretaria_pode_criar_nova_matricula_apos_encerrar_anterior(
        self, client, user_secretaria, user_aluno, turma, status_final
    ):
        matricula_anterior = Matricula.objects.create(aluno=user_aluno, turma=turma)
        client.force_login(user_secretaria)
        client.post(
            reverse('enrollment:matricula_status', args=[matricula_anterior.pk]),
            data={'status': status_final},
        )

        response = client.post(
            reverse('enrollment:matricula_create'),
            data={'aluno': user_aluno.pk, 'turma': turma.pk},
        )

        assert response.status_code == 302
        matricula_anterior.refresh_from_db()
        nova_matricula = Matricula.objects.get(
            aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA
        )
        assert nova_matricula.pk != matricula_anterior.pk
        assert matricula_anterior.status == status_final

    def test_rota_de_status_exige_post(self, client, user_secretaria, user_aluno, turma):
        matricula = Matricula.objects.create(aluno=user_aluno, turma=turma)
        client.force_login(user_secretaria)

        response = client.get(reverse('enrollment:matricula_status', args=[matricula.pk]))

        assert response.status_code == 405
