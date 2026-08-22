import pytest
from django.urls import reverse
from apps.accounts.models import CustomUser, UserRole
from apps.accounts.services import toggle_user_active_status

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
