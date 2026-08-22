import pytest
from django.urls import reverse
from apps.accounts.models import CustomUser, UserRole
from apps.accounts.services import toggle_user_active_status

@pytest.mark.django_db
class TestUserManagement:
    def test_secretaria_can_list_users(self, client, secretaria_user):
        client.force_login(secretaria_user)
        response = client.get(reverse('accounts:usuario_list'))
        assert response.status_code == 200
        assert 'usuarios' in response.context

    def test_aluno_cannot_access_user_management(self, client, aluno_user):
        client.force_login(aluno_user)
        response = client.get(reverse('accounts:usuario_list'))
        assert response.status_code == 403

    def test_create_aluno_validates_unique_email(self, client, secretaria_user, aluno_user):
        client.force_login(secretaria_user)
        data = {
            'full_name': 'Novo Aluno',
            'email': aluno_user.email  # E-mail ja existente
        }
        response = client.post(reverse('accounts:usuario_create') + '?tipo=aluno', data=data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'email' in response.context['form'].errors

    def test_toggle_user_active_status(self, aluno_user):
        assert aluno_user.is_active is True
        toggle_user_active_status(aluno_user)
        aluno_user.refresh_from_db()
        assert aluno_user.is_active is False
        
        toggle_user_active_status(aluno_user)
        aluno_user.refresh_from_db()
        assert aluno_user.is_active is True

    def test_inactive_user_cannot_login(self, client, aluno_user):
        # Desativa o aluno
        aluno_user.is_active = False
        aluno_user.set_password('senha123')
        aluno_user.save()
        
        # Tenta logar
        response = client.post(reverse('accounts:login'), {
            'username': aluno_user.email,
            'password': 'senha123'
        })
        # A pagina recarrega com a mensagem de erro (nao redireciona pro dashboard)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Sua conta está inativa' in content or 'conta de usuário está inativa' in content
