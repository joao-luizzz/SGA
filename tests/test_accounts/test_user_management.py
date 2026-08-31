import pytest
from django.urls import reverse
from django.contrib.auth import authenticate
from accounts.models import CustomUser, UserRole
from accounts.services import toggle_user_active_status

@pytest.mark.django_db
class TestUserManagement:
    def test_secretaria_can_list_users(self, client, user_secretaria):
        client.force_login(user_secretaria)
        response = client.get(reverse('accounts:usuario_list'))
        assert response.status_code == 200
        assert 'usuarios' in response.context

    def test_aluno_cannot_access_user_management(self, client, user_aluno):
        client.force_login(user_aluno)
        response = client.get(reverse('accounts:usuario_list'))
        assert response.status_code == 403

    def test_create_aluno_validates_unique_email(self, client, user_secretaria, user_aluno):
        client.force_login(user_secretaria)
        data = {
            'full_name': 'Novo Aluno',
            'email': user_aluno.email  # E-mail ja existente
        }
        response = client.post(reverse('accounts:usuario_create') + '?tipo=aluno', data=data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'email' in response.context['form'].errors

    def test_secretaria_creates_user_with_authenticatable_temporary_password(
        self, client, user_secretaria
    ):
        client.force_login(user_secretaria)
        temporary_password = 'SenhaTemporaria@2026'

        response = client.post(
            reverse('accounts:usuario_create') + '?tipo=aluno',
            data={
                'full_name': 'Novo Aluno',
                'email': 'novo.aluno@example.com',
                'password1': temporary_password,
                'password2': temporary_password,
            },
        )

        assert response.status_code == 302
        user = CustomUser.objects.get(email='novo.aluno@example.com')
        assert user.role == UserRole.ALUNO
        assert user.must_change_password is True
        assert user.password != temporary_password
        assert authenticate(username=user.email, password=temporary_password) == user

    def test_invalid_user_type_is_rejected(self, client, user_secretaria):
        client.force_login(user_secretaria)

        response = client.get(reverse('accounts:usuario_create') + '?tipo=secretaria')

        assert response.status_code == 400

    @pytest.mark.parametrize('usuario_fixture', ['user_aluno', 'user_professor'])
    def test_secretaria_edita_aluno_e_professor(
        self, client, request, user_secretaria, usuario_fixture
    ):
        usuario = request.getfixturevalue(usuario_fixture)
        client.force_login(user_secretaria)
        email_normalizado = f'novo.{usuario.role.lower()}@sga.edu.br'

        response = client.post(
            reverse('accounts:usuario_edit', args=[usuario.pk]),
            data={
                'full_name': f'{usuario.full_name} Atualizado',
                'email': f'  {email_normalizado.upper()}  ',
            },
        )

        assert response.status_code == 302
        usuario.refresh_from_db()
        assert usuario.full_name.endswith('Atualizado')
        assert usuario.email == email_normalizado

    def test_edicao_normaliza_email_e_rejeita_duplicidade(
        self, client, user_secretaria, user_aluno, user_professor
    ):
        client.force_login(user_secretaria)

        response = client.post(
            reverse('accounts:usuario_edit', args=[user_aluno.pk]),
            data={
                'full_name': user_aluno.full_name,
                'email': f'  {user_professor.email.upper()}  ',
            },
        )

        assert response.status_code == 200
        assert 'email' in response.context['form'].errors
        user_aluno.refresh_from_db()
        assert user_aluno.email == 'aluno@sga.edu.br'

    @pytest.mark.parametrize(
        'usuario_fixture', ['user_aluno', 'user_professor', 'user_coordenacao']
    )
    def test_outros_perfis_nao_acessam_edicao_de_usuario(
        self, client, request, usuario_fixture, user_aluno
    ):
        client.force_login(request.getfixturevalue(usuario_fixture))

        response = client.get(reverse('accounts:usuario_edit', args=[user_aluno.pk]))

        assert response.status_code == 403

    @pytest.mark.parametrize('usuario_fixture', ['user_secretaria', 'user_coordenacao'])
    def test_secretaria_nao_edita_contas_nao_gerenciaveis(
        self, client, request, user_secretaria, usuario_fixture
    ):
        usuario = request.getfixturevalue(usuario_fixture)
        client.force_login(user_secretaria)

        response = client.get(reverse('accounts:usuario_edit', args=[usuario.pk]))

        assert response.status_code == 403

    def test_secretaria_nao_edita_outra_conta_de_secretaria(
        self, client, user_secretaria
    ):
        outra_secretaria = CustomUser.objects.create_user(
            email='outra.secretaria@sga.edu.br',
            full_name='Outra Secretaria',
            role=UserRole.SECRETARIA,
            password='SenhaSegura123!',
        )
        client.force_login(user_secretaria)

        response = client.get(
            reverse('accounts:usuario_edit', args=[outra_secretaria.pk])
        )

        assert response.status_code == 403

    def test_edicao_preserva_senha_role_e_flags(
        self, client, user_secretaria, user_professor, password
    ):
        user_professor.must_change_password = True
        user_professor.is_active = False
        user_professor.save(update_fields=['must_change_password', 'is_active'])
        client.force_login(user_secretaria)

        response = client.post(
            reverse('accounts:usuario_edit', args=[user_professor.pk]),
            data={'full_name': 'Professor Preservado', 'email': 'professor.editado@sga.edu.br'},
        )

        assert response.status_code == 302
        user_professor.refresh_from_db()
        assert user_professor.role == UserRole.PROFESSOR
        assert user_professor.must_change_password is True
        assert user_professor.is_active is False
        assert user_professor.check_password(password)

    def test_listagem_exibe_link_de_edicao(self, client, user_secretaria, user_aluno):
        client.force_login(user_secretaria)

        response = client.get(reverse('accounts:usuario_list'))

        assert reverse('accounts:usuario_edit', args=[user_aluno.pk]).encode() in response.content

    def test_secretaria_cannot_toggle_own_account(self, client, user_secretaria):
        client.force_login(user_secretaria)

        response = client.post(
            reverse('accounts:usuario_toggle_active', args=[user_secretaria.pk])
        )

        assert response.status_code == 302
        user_secretaria.refresh_from_db()
        assert user_secretaria.is_active is True

    def test_toggle_user_active_status(self, user_aluno):
        assert user_aluno.is_active is True
        toggle_user_active_status(user_aluno)
        user_aluno.refresh_from_db()
        assert user_aluno.is_active is False
        
        toggle_user_active_status(user_aluno)
        user_aluno.refresh_from_db()
        assert user_aluno.is_active is True

    def test_inactive_user_cannot_login(self, client, user_aluno):
        # Desativa o aluno
        user_aluno.is_active = False
        user_aluno.set_password('senha123')
        user_aluno.save()
        
        # Tenta logar
        response = client.post(reverse('accounts:login'), {
            'username': user_aluno.email,
            'password': 'senha123'
        })
        # A pagina recarrega com a mensagem de erro (nao redireciona pro dashboard)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Sua conta está inativa' in content or 'conta de usuário está inativa' in content
