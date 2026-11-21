import csv
from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse

from accounts.models import CustomUser
from academics.models import Curso, Turma
from assessments.models import Nota
from attendance.models import Falta
from enrollment.models import Matricula
from transfers.models import SolicitacaoTransferencia


@pytest.fixture
def semana5_demo(db):
    call_command('seed_demo', stdout=StringIO())
    return {
        chave: CustomUser.objects.get(email=email) for chave, email in {
            'secretaria': 'secretaria.demo@sga.edu.br',
            'coordenacao': 'coordenacao.demo@sga.edu.br',
            'professor': 'professor.demo@sga.edu.br',
            'aluno': 'aluno.exame@sga.edu.br',
            'outro': 'aluno.aprovado@sga.edu.br',
        }.items()
    }


@pytest.mark.django_db
@pytest.mark.parametrize('tipo', ['ENTRADA', 'SAIDA'])
@pytest.mark.parametrize('decisao', ['APROVADA', 'RECUSADA'])
def test_semana5_demo_fluxos_preservam_relatorios_filtrados(client, semana5_demo, tipo, decisao):
    usuarios = semana5_demo
    curso = Curso.objects.get(codigo='ADS-DEMO')
    turma = Turma.objects.get(disciplina__codigo='ES-DEMO')
    filtros = {'curso': curso.pk, 'turma': turma.pk, 'periodo': '2026/2', 'risco': 'sim'}
    client.force_login(usuarios['coordenacao'])
    csv_antes = client.get(reverse('academics:relatorios_csv'), filtros)
    assert csv_antes.status_code == 200
    linhas = list(csv.DictReader(StringIO(csv_antes.content.decode('utf-8-sig'))))
    assert {linha['Aluno'] for linha in linhas} == {'Aluno Elegível ao Exame', 'Aluno Reprovado por Falta'}
    assert all(linha['Acompanhamento'] == 'Em risco / atenção' for linha in linhas)
    modelos = [Matricula, Nota, Falta]
    historico = {modelo: list(modelo.objects.order_by('pk').values()) for modelo in modelos}

    client.force_login(usuarios['secretaria'])
    dados = {'aluno': usuarios['aluno'].pk, 'curso': curso.pk, 'tipo': tipo,
             'instituicao_externa': 'Instituição Demonstração', 'curso_externo': 'ADS Externo',
             'data_referencia': date(2026, 9, 24), 'documentos': 'Histórico conferido; cenário de teste.'}
    resposta = client.post(reverse('transfers:criar'), dados, follow=True)
    assert resposta.status_code == 200
    registro = SolicitacaoTransferencia.objects.get()
    assert registro.status == 'PENDENTE'
    # Duplicidade tratada na tela, sem segundo registro.
    assert client.post(reverse('transfers:criar'), dados).context['form'].errors
    assert SolicitacaoTransferencia.objects.count() == 1
    url = reverse('transfers:analisar', args=[registro.pk])
    assert client.post(url, {'decisao': decisao, 'justificativa': 'Sem permissão'}).status_code == 403
    client.force_login(usuarios['coordenacao'])
    assert client.post(url, {'decisao': decisao}).status_code == 400
    assert client.post(url, {'decisao': decisao, 'justificativa': 'Conferência integrada.'}, follow=True).status_code == 200
    registro.refresh_from_db()
    assert registro.status == decisao
    assert client.post(url, {'decisao': decisao, 'justificativa': 'Reenvio'}).status_code == 400
    assert client.get(reverse('academics:relatorios_csv'), filtros).content == csv_antes.content
    pagina = client.get(reverse('academics:relatorios'), filtros)
    assert len(pagina.context['linhas']) == 2
    assert pagina.context['turmas'][0].matriculas_ativas == 3
    for modelo in modelos:
        assert list(modelo.objects.order_by('pk').values()) == historico[modelo]

    client.force_login(usuarios['aluno'])
    assert client.get(reverse('transfers:detalhe', args=[registro.pk])).status_code == 200
    assert client.get(reverse('academics:relatorios'), filtros).status_code == 403
    client.force_login(usuarios['outro'])
    assert client.get(reverse('transfers:detalhe', args=[registro.pk])).status_code == 404
    client.force_login(usuarios['professor'])
    assert client.get(reverse('transfers:index')).status_code == 403
    assert client.get(reverse('academics:relatorios_csv'), filtros).status_code == 403
