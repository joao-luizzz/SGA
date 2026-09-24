from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.urls import reverse

from academics.models import Disciplina, Turma
from accounts.models import AuditoriaLog, CustomUser
from assessments.models import Nota
from attendance.models import Falta
from enrollment.models import Matricula
from transfers.models import SolicitacaoTransferencia
from transfers.services import analisar_transferencia, solicitar_transferencia


@pytest.mark.django_db
@pytest.mark.parametrize('tipo', ['ENTRADA', 'SAIDA'])
@pytest.mark.parametrize('decisao', ['APROVADA', 'RECUSADA'])
def test_fluxo_preserva_historico_e_relatorios(client, dados_transferencia, user_professor, user_coordenacao, tipo, decisao):
    disciplina = Disciplina.objects.create(nome='Algoritmos', codigo='ALG-T', carga_horaria=60,
                                           curso=dados_transferencia['curso'])
    turma = Turma.objects.create(disciplina=disciplina, professor=user_professor,
                                 periodo_letivo='2026.2', horarios='SEG 08:00-10:00',
                                 sala='A1', vagas_maximas=30)
    aluno = dados_transferencia['aluno']
    # Inclui uma tentativa histórica e outra ativa; nenhuma deve ser apagada ou alterada.
    antiga = Matricula.objects.create(aluno=aluno, turma=turma, status='CANCELADA')
    atual = Matricula.objects.create(aluno=aluno, turma=turma)
    for matricula in [antiga, atual]:
        for tipo_nota in ['P1', 'P2', 'TRABALHO']:
            Nota.objects.create(matricula=matricula, tipo=tipo_nota, valor=Decimal('0.00'),
                                registrado_por=user_professor)
    Falta.objects.create(aluno=aluno, turma=turma, data_aula=date(2026, 9, 1),
                         presente=False, registrado_por=user_professor)
    modelos = [Matricula, Nota, Falta, CustomUser]
    client.force_login(user_coordenacao)
    antes = {modelo: list(modelo.objects.order_by('pk').values()) for modelo in modelos}
    url_csv = reverse('academics:relatorios_csv')
    csv_antes = client.get(url_csv)
    assert csv_antes.status_code == 200
    registro = solicitar_transferencia(**{**dados_transferencia, 'tipo': tipo})
    resposta = client.post(reverse('transfers:analisar', args=[registro.pk]),
                           {'decisao': decisao, 'justificativa': 'Documentos conferidos.'}, follow=True)
    assert resposta.status_code == 200
    registro.refresh_from_db()
    assert registro.status == decisao
    for modelo in modelos:
        assert list(modelo.objects.order_by('pk').values()) == antes[modelo]
    assert client.get(url_csv).content == csv_antes.content
    assert client.get(reverse('academics:relatorios')).status_code == 200
    assert AuditoriaLog.objects.filter(tabela_afetada='SolicitacaoTransferencia').count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('operacao', ['solicitar', 'decidir'])
def test_concorrencia_real_postgresql(dados_transferencia, user_coordenacao, operacao):
    if connection.vendor != 'postgresql':
        pytest.skip('Locks concorrentes precisam do PostgreSQL; executado no job PostgreSQL do CI.')
    registro = solicitar_transferencia(**dados_transferencia) if operacao == 'decidir' else None
    barreira = Barrier(2)

    def executar(indice):
        close_old_connections()
        try:
            barreira.wait(timeout=10)
            try:
                if operacao == 'solicitar':
                    solicitar_transferencia(**dados_transferencia)
                else:
                    analisar_transferencia(usuario=user_coordenacao, solicitacao_id=registro.pk,
                                           decisao=['APROVADA', 'RECUSADA'][indice],
                                           justificativa=f'Análise concorrente {indice}')
                return 'sucesso'
            except ValidationError:
                return 'rejeitada'
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(executar, indice) for indice in range(2)]
        resultados = [futuro.result(timeout=30) for futuro in futuros]
    assert sorted(resultados) == ['rejeitada', 'sucesso']
    assert SolicitacaoTransferencia.objects.count() == 1
    assert AuditoriaLog.objects.filter(acao='CRIAR').count() == 1
    assert AuditoriaLog.objects.filter(acao='EDITAR').count() == (1 if operacao == 'decidir' else 0)
