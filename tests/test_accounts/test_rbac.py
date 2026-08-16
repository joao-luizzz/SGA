import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestRoleBasedAccessControl:
    def test_aluno_cannot_access_secretaria_dashboard(self, client, user_aluno, password):
        client.login(username=user_aluno.email, password=password)
        secretaria_url = reverse('accounts:dashboard_secretaria')
        response = client.get(secretaria_url)
        assert response.status_code == 403

    def test_aluno_cannot_access_coordenacao_dashboard(self, client, user_aluno, password):
        client.login(username=user_aluno.email, password=password)
        coordenacao_url = reverse('accounts:dashboard_coordenacao')
        response = client.get(coordenacao_url)
        assert response.status_code == 403

    def test_professor_cannot_access_coordenacao_dashboard(self, client, user_professor, password):
        client.login(username=user_professor.email, password=password)
        coordenacao_url = reverse('accounts:dashboard_coordenacao')
        response = client.get(coordenacao_url)
        assert response.status_code == 403

    def test_secretaria_access_secretaria_dashboard(self, client, user_secretaria, password):
        client.login(username=user_secretaria.email, password=password)
        secretaria_url = reverse('accounts:dashboard_secretaria')
        response = client.get(secretaria_url)
        assert response.status_code == 200

    def test_coordenacao_access_coordenacao_dashboard(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        coordenacao_url = reverse('accounts:dashboard_coordenacao')
        response = client.get(coordenacao_url)
        assert response.status_code == 200

    def test_unauthenticated_user_redirected_to_login(self, client):
        dashboard_url = reverse('accounts:dashboard_aluno')
        response = client.get(dashboard_url)
        assert response.status_code == 302
        assert reverse('accounts:login') in response.url
