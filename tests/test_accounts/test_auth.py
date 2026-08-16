import pytest
from django.urls import reverse
from accounts.models import CustomUser

@pytest.mark.django_db
class TestAuthenticationFlows:
    def test_login_valid_credentials(self, client, user_aluno, password):
        login_url = reverse('accounts:login')
        response = client.post(login_url, {
            'username': user_aluno.email,
            'password': password
        })
        assert response.status_code == 302
        assert response.url == reverse('accounts:dashboard_aluno')

    def test_login_inactive_user(self, client, user_inactive, password):
        login_url = reverse('accounts:login')
        response = client.post(login_url, {
            'username': user_inactive.email,
            'password': password
        })
        assert response.status_code == 200
        assert "E-mail ou senha incorretos" in response.content.decode('utf-8') or "inativa" in response.content.decode('utf-8')

    def test_mandatory_password_change_redirect(self, client, user_must_change_pw, password):
        login_url = reverse('accounts:login')
        response = client.post(login_url, {
            'username': user_must_change_pw.email,
            'password': password
        }, follow=True)

        assert response.status_code == 200
        assert reverse('accounts:change_password') in response.redirect_chain[0][0]

    def test_password_change_success(self, client, user_must_change_pw, password):
        client.login(username=user_must_change_pw.email, password=password)
        change_url = reverse('accounts:change_password')

        new_pw = "NovaSenhaSegura456!"
        response = client.post(change_url, {
            'new_password1': new_pw,
            'new_password2': new_pw
        })

        assert response.status_code == 302
        user_must_change_pw.refresh_from_db()
        assert user_must_change_pw.must_change_password is False
        assert user_must_change_pw.check_password(new_pw) is True

    def test_logout_view(self, client, user_aluno, password):
        client.login(username=user_aluno.email, password=password)
        logout_url = reverse('accounts:logout')
        response = client.get(logout_url)
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')
