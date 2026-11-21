import pytest
from django.urls import reverse

from tests.test_academics.test_reports import dados_relatorio, _criar_notas

pytestmark = pytest.mark.django_db


def test_tela_imprimivel_contem_alerta_filtros_e_exportacao(client, user_coordenacao, user_professor, dados_relatorio):
    matricula = dados_relatorio['matricula']
    _criar_notas(matricula, user_professor, {'P1': '0.00'})
    client.force_login(user_coordenacao)
    resposta = client.get(reverse('academics:relatorios'), {'turma': matricula.turma_id, 'risco': 'sim'})
    conteudo = resposta.content.decode()
    assert 'imprimir-relatorio' in conteudo
    assert 'css/relatorios.css' in conteudo and 'js/relatorios.js' in conteudo
    assert 'risco=sim' in conteudo
    assert 'Em risco / atenção' in conteudo and 'avaliações incompletas' in conteudo
    assert 'Sem aulas registradas' in conteudo
    assert 'Gerado em' in conteudo


def test_tela_escapa_texto_em_relatorio(client, user_coordenacao, dados_relatorio):
    aluno = dados_relatorio['matricula'].aluno
    aluno.full_name = '<script>alert(1)</script>'
    aluno.save(update_fields=['full_name'])
    client.force_login(user_coordenacao)
    conteudo = client.get(reverse('academics:relatorios')).content.decode()
    assert '<script>alert(1)</script>' not in conteudo
    assert '&lt;script&gt;' in conteudo
