import pytest
from django.urls import reverse
from communications.models import Comunicado, EscopoComunicado


@pytest.mark.django_db
class TestComunicadoViews:
    @pytest.fixture
    def setup_comunicado(self, user_secretaria):
        return Comunicado.objects.create(
            autor=user_secretaria,
            titulo="Aviso Geral Importante",
            conteudo="Comunicado de teste para todas as turmas.",
            escopo=EscopoComunicado.GERAL
        )

    def test_mural_view_usuario_autenticado(self, client, user_aluno, password, setup_comunicado):
        client.login(email=user_aluno.email, password=password)
        resp = client.get(reverse('communications:mural'))
        assert resp.status_code == 200
        assert "Aviso Geral Importante" in resp.content.decode('utf-8')
        assert resp.context['pode_gerenciar'] is False

    def test_comunicado_detail_view(self, client, user_aluno, password, setup_comunicado):
        client.login(email=user_aluno.email, password=password)
        resp = client.get(reverse('communications:detail', kwargs={'pk': setup_comunicado.pk}))
        assert resp.status_code == 200
        assert "Aviso Geral Importante" in resp.content.decode('utf-8')

    def test_secretaria_acessa_gestao_e_ve_botao_criar(self, client, user_secretaria, password, setup_comunicado):
        client.login(email=user_secretaria.email, password=password)
        resp = client.get(reverse('communications:gestao'))
        assert resp.status_code == 200
        assert "Painel de Gestão de Comunicados" in resp.content.decode('utf-8')

    def test_aluno_bloqueado_no_painel_de_gestao(self, client, user_aluno, password):
        client.login(email=user_aluno.email, password=password)
        resp = client.get(reverse('communications:gestao'))
        assert resp.status_code == 403

    def test_secretaria_cria_comunicado_via_post(self, client, user_secretaria, password):
        client.login(email=user_secretaria.email, password=password)
        url_create = reverse('communications:create')

        resp_get = client.get(url_create)
        assert resp_get.status_code == 200

        resp = client.post(url_create, {
            'titulo': 'Novo Aviso da Secretaria',
            'conteudo': 'Documentos devem ser entregues até sexta.',
            'escopo': 'GERAL',
            'ativo': 'on'
        })
        assert resp.status_code == 302
        assert Comunicado.objects.filter(titulo='Novo Aviso da Secretaria').exists()

    def test_secretaria_edita_comunicado_via_post(self, client, user_secretaria, password, setup_comunicado):
        client.login(email=user_secretaria.email, password=password)
        url_edit = reverse('communications:update', kwargs={'pk': setup_comunicado.pk})

        resp_get = client.get(url_edit)
        assert resp_get.status_code == 200

        resp_post = client.post(url_edit, {
            'titulo': 'Aviso Geral Editado',
            'conteudo': 'Texto editado',
            'escopo': 'GERAL',
            'ativo': 'on'
        })
        assert resp_post.status_code == 302
        setup_comunicado.refresh_from_db()
        assert setup_comunicado.titulo == 'Aviso Geral Editado'

    def test_inativar_comunicado_via_post(self, client, user_secretaria, password, setup_comunicado):
        client.login(email=user_secretaria.email, password=password)
        url_inativar = reverse('communications:inativar', kwargs={'pk': setup_comunicado.pk})
        resp = client.post(url_inativar)
        assert resp.status_code == 302
        setup_comunicado.refresh_from_db()
        assert setup_comunicado.ativo is False
