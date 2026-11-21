import csv
from io import StringIO

import pytest
from django.urls import reverse

from academics.selectors import get_relatorio_turmas
from tests.test_academics.test_reports import dados_relatorio, _criar_aluno, _criar_notas
from enrollment.models import Matricula

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('url', ['academics:relatorios', 'academics:relatorios_csv'])
@pytest.mark.parametrize('parametros', [
    {'curso': 'abc'}, {'turma': '-1'}, {'curso': '0'}, {'turma': str(2**64)},
    {'periodo': 'x'*11}, {'risco': 'talvez'},
])
def test_filtros_invalidos_retornam_400(client, user_coordenacao, url, parametros):
    client.force_login(user_coordenacao)
    assert client.get(reverse(url), parametros).status_code == 400


def test_filtro_risco_nao_altera_ocupacao_e_csv_corresponde(client, user_coordenacao, user_professor, dados_relatorio, django_assert_num_queries):
    matricula = dados_relatorio['matricula']
    _criar_notas(matricula, user_professor, {'P1': '0.00'})
    outra = Matricula.objects.create(turma=matricula.turma, aluno=_criar_aluno(99))
    _criar_notas(outra, user_professor, {'P1': '8.00'})
    with django_assert_num_queries(4):
        relatorio = get_relatorio_turmas(turma_id=matricula.turma_id, risco='sim')
    assert [linha['matricula'].pk for linha in relatorio['linhas']] == [matricula.pk]
    assert relatorio['turmas'][0].matriculas_ativas == 2
    assert [linha['matricula'].pk for linha in get_relatorio_turmas(risco='nao')['linhas']] == [outra.pk]
    client.force_login(user_coordenacao)
    parametros = {'curso': matricula.turma.disciplina.curso_id, 'turma': matricula.turma_id,
                  'periodo': matricula.turma.periodo_letivo, 'risco': 'sim'}
    pagina = client.get(reverse('academics:relatorios'), parametros)
    exportacao = client.get(reverse('academics:relatorios_csv'), parametros)
    linhas = list(csv.DictReader(StringIO(exportacao.content.decode('utf-8-sig'))))
    assert len(linhas) == len(pagina.context['linhas']) == 1
    assert linhas[0]['Matricula'] == str(matricula.pk)
    assert linhas[0]['P1'] == '0.00'
    assert linhas[0]['Matriculados ativos'] == '2'
    assert linhas[0]['Acompanhamento'] == 'Em risco / atenção'
    assert 'incompletas' in linhas[0]['Motivos de atencao']


def test_filtros_contraditorios_retornam_vazio(dados_relatorio):
    assert get_relatorio_turmas(curso_id=dados_relatorio['curso_si'].pk,
                               turma_id=dados_relatorio['turma_ads_1'].pk)['linhas'] == []
