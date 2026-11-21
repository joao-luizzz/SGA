import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import CustomUser
from transfers.models import SolicitacaoTransferencia
from transfers.selectors import listar_transferencias
from transfers.services import solicitar_transferencia

pytestmark = pytest.mark.django_db


def formulario(dados):
    return {chave: valor.pk if hasattr(valor, 'pk') else valor
            for chave, valor in dados.items() if chave != 'usuario'}


def test_secretaria_cria_e_consulta_pela_interface(client, dados_transferencia):
    client.force_login(dados_transferencia['usuario'])
    url = reverse('transfers:criar')
    assert client.get(url).status_code == 200
    resposta = client.post(url, formulario(dados_transferencia), follow=True)
    assert resposta.status_code == 200
    registro = SolicitacaoTransferencia.objects.get()
    assert resposta.request['PATH_INFO'] == reverse('transfers:detalhe', args=[registro.pk])
    assert 'pendente' in resposta.content.decode().lower()
    assert 'Universidade Externa' in resposta.content.decode()
    assert client.get(reverse('transfers:index')).status_code == 200


def test_formulario_obrigatorio_e_duplicidade_exibem_erros(client, solicitacao, dados_transferencia):
    client.force_login(dados_transferencia['usuario'])
    url = reverse('transfers:criar')
    resposta = client.post(url, {})
    assert resposta.context['form'].errors
    resposta = client.post(url, formulario(dados_transferencia))
    assert resposta.context['form'].non_field_errors()
    assert SolicitacaoTransferencia.objects.count() == 1


@pytest.mark.parametrize('perfil', ['user_aluno', 'user_professor', 'user_coordenacao'])
def test_acesso_direto_criacao_proibido(client, perfil, request):
    client.force_login(request.getfixturevalue(perfil))
    for metodo in [client.get, client.post]:
        assert metodo(reverse('transfers:criar')).status_code == 403


@pytest.mark.parametrize('perfil', ['user_aluno', 'user_professor', 'user_secretaria'])
def test_post_decisao_sem_permissao(client, solicitacao, perfil, request):
    client.force_login(request.getfixturevalue(perfil))
    resposta = client.post(reverse('transfers:analisar', args=[solicitacao.pk]),
                           {'decisao': 'APROVADA', 'justificativa': 'Tentativa indevida'})
    assert resposta.status_code == 403
    solicitacao.refresh_from_db()
    assert solicitacao.status == 'PENDENTE'


def test_aluno_so_consulta_propria_solicitacao(client, solicitacao, dados_transferencia):
    outro = CustomUser.objects.create_user(email='outro@teste.edu', full_name='Outro Aluno', role='ALUNO')
    alheia = solicitar_transferencia(**{**dados_transferencia, 'aluno': outro})
    client.force_login(solicitacao.aluno)
    resposta = client.get(reverse('transfers:index'))
    assert list(resposta.context['page_obj']) == [solicitacao]
    assert 'Outro Aluno' not in resposta.content.decode()
    assert client.get(reverse('transfers:detalhe', args=[solicitacao.pk])).status_code == 200
    assert client.get(reverse('transfers:detalhe', args=[alheia.pk])).status_code == 404
    resposta = client.get(reverse('transfers:index'), {'curso': alheia.curso_id})
    assert list(resposta.context['page_obj']) == [solicitacao]


def test_professor_nao_consulta(client, user_professor, solicitacao):
    client.force_login(user_professor)
    assert client.get(reverse('transfers:index')).status_code == 403
    assert client.get(reverse('transfers:detalhe', args=[solicitacao.pk])).status_code == 403


def test_anonimo_redirecionado(client):
    assert client.get(reverse('transfers:index')).status_code == 302


@pytest.mark.parametrize('decisao', ['APROVADA', 'RECUSADA'])
def test_coordenacao_decide_e_reenvio_nao_repete(client, solicitacao, user_coordenacao, decisao):
    client.force_login(user_coordenacao)
    detalhe = reverse('transfers:detalhe', args=[solicitacao.pk])
    assert client.get(detalhe).context['pode_analisar']
    url = reverse('transfers:analisar', args=[solicitacao.pk])
    assert client.get(url).status_code == 405
    dados = {'decisao': decisao, 'justificativa': 'Análise concluída.'}
    resposta = client.post(url, dados, follow=True)
    assert resposta.status_code == 200
    assert not resposta.context['pode_analisar']
    assert 'Análise concluída.' in resposta.content.decode()
    resposta = client.post(url, dados)
    assert resposta.status_code == 400
    assert 'já foi analisada' in resposta.content.decode()


def test_justificativa_obrigatoria_na_tela(client, solicitacao, user_coordenacao):
    client.force_login(user_coordenacao)
    resposta = client.post(reverse('transfers:analisar', args=[solicitacao.pk]), {'decisao': 'RECUSADA'})
    assert resposta.status_code == 400
    assert 'justificativa' in resposta.context['form'].errors


def test_csrf_exigido(solicitacao, user_coordenacao):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_coordenacao)
    assert client.post(reverse('transfers:analisar', args=[solicitacao.pk]),
                       {'decisao': 'APROVADA', 'justificativa': 'OK'}).status_code == 403


def test_filtros_invalidos_e_lista_vazia(client, user_secretaria):
    client.force_login(user_secretaria)
    resposta = client.get(reverse('transfers:index'))
    assert resposta.status_code == 200 and not list(resposta.context['page_obj'])
    for filtros in [{'status': 'INVALIDO'}, {'tipo': 'INVALIDO'}, {'curso': '-1'}]:
        assert client.get(reverse('transfers:index'), filtros).status_code == 400


def test_consultas_relacionadas_nao_crescem_por_linha(solicitacao, dados_transferencia, django_assert_num_queries):
    solicitar_transferencia(**{**dados_transferencia, 'instituicao_externa': 'Segunda instituição'})
    with django_assert_num_queries(2):  # perfil persistido + consulta com joins
        registros = listar_transferencias(usuario=dados_transferencia['usuario'])
        for registro in registros:
            assert registro.aluno.full_name and registro.curso.nome
            assert registro.solicitada_por.full_name and registro.origem and registro.destino


def test_paginacao_e_filtros_preservados(client, solicitacao, dados_transferencia):
    for indice in range(20):
        solicitar_transferencia(**{**dados_transferencia, 'instituicao_externa': f'Instituição {indice}'})
    client.force_login(dados_transferencia['usuario'])
    resposta = client.get(reverse('transfers:index'), {'status': 'PENDENTE', 'tipo': 'SAIDA', 'page': 2})
    assert len(resposta.context['page_obj']) == 1
    assert resposta.context['page_obj'].paginator.count == 21
    assert 'status=PENDENTE' in resposta.context['parametros']


def test_texto_externo_escapado(client, dados_transferencia):
    registro = solicitar_transferencia(**{**dados_transferencia, 'documentos': '<script>alert(1)</script>'})
    client.force_login(dados_transferencia['usuario'])
    conteudo = client.get(reverse('transfers:detalhe', args=[registro.pk])).content.decode()
    assert '<script>alert(1)</script>' not in conteudo
    assert '&lt;script&gt;' in conteudo
