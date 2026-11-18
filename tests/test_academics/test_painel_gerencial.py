from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse

from academics.models import Curso, Disciplina, Turma
from academics.selectors import get_indicadores_gerenciais
from academics.services import registrar_aproveitamento
from accounts.models import CustomUser, UserRole
from assessments.models import Nota, TipoAvaliacao
from assessments.selectors import SituacaoAcademica
from enrollment.models import Matricula
from transfers.services import solicitar_transferencia


def _aluno(indice):
    return CustomUser.objects.create_user(
        email=f'aluno{indice}@sga.edu.br', full_name=f'Aluno {indice}',
        role=UserRole.ALUNO, password='x', must_change_password=False,
    )


def _notas(matricula, professor, p1, p2, trabalho):
    for tipo, valor in ((TipoAvaliacao.P1, p1), (TipoAvaliacao.P2, p2), (TipoAvaliacao.TRABALHO, trabalho)):
        Nota.objects.create(matricula=matricula, tipo=tipo, valor=Decimal(valor), registrado_por=professor)


@pytest.fixture
def cenario(db, user_professor):
    si = Curso.objects.create(nome='Sistemas', codigo='SI')
    direito = Curso.objects.create(nome='Direito', codigo='DIR')
    algoritmos = Disciplina.objects.create(nome='Algoritmos', codigo='ALG', carga_horaria=80, curso=si)
    civil = Disciplina.objects.create(nome='Civil', codigo='CIV', carga_horaria=60, curso=direito)
    turma_si = Turma.objects.create(disciplina=algoritmos, periodo_letivo='2026/2', horarios='SEG 08:00-10:00',
                                    sala='A1', vagas_maximas=4, professor=user_professor)
    turma_dir = Turma.objects.create(disciplina=civil, periodo_letivo='2026/1', horarios='TER 08:00-10:00',
                                     sala='B1', vagas_maximas=10, professor=user_professor)
    alunos = [_aluno(i) for i in range(4)]
    aprovado = Matricula.objects.create(aluno=alunos[0], turma=turma_si)
    _notas(aprovado, user_professor, 8, 8, 8)
    reprovado = Matricula.objects.create(aluno=alunos[1], turma=turma_si)
    _notas(reprovado, user_professor, 2, 2, 2)
    Matricula.objects.create(aluno=alunos[2], turma=turma_si)          # em andamento
    Matricula.objects.create(aluno=alunos[3], turma=turma_dir)         # em andamento, outro curso
    return {'si': si, 'direito': direito, 'algoritmos': algoritmos, 'alunos': alunos}


@pytest.mark.django_db
def test_indicadores_agregam_ocupacao_situacao_e_risco(cenario):
    dados = get_indicadores_gerenciais()

    assert dados['totais']['turmas'] == 2
    assert dados['totais']['matriculas'] == 4
    assert dados['totais']['vagas'] == 14
    assert dados['totais']['ocupacao'] == 29
    assert dados['totais']['taxa_aprovacao'] == 50
    assert dados['totais']['concluidos'] == 2
    assert dados['totais']['em_risco'] == 1
    assert dados['matriculas_por_curso'] == [('Direito', 1), ('Sistemas', 3)]
    assert dados['ocupacao'][0]['percentual'] == 75
    contagem = {item['situacao']: item['quantidade'] for item in dados['distribuicao']}
    assert contagem[SituacaoAcademica.APROVADO_DIRETO] == 1
    assert contagem[SituacaoAcademica.REPROVADO_NOTA] == 1
    assert contagem[SituacaoAcademica.EM_ANDAMENTO] == 2


@pytest.mark.django_db
def test_indicadores_respeitam_filtros_de_curso_e_periodo(cenario):
    por_curso = get_indicadores_gerenciais(curso_id=cenario['direito'].pk)
    por_periodo = get_indicadores_gerenciais(periodo='2026/2')

    assert por_curso['totais']['matriculas'] == 1
    assert por_curso['totais']['taxa_aprovacao'] is None
    assert por_periodo['matriculas_por_curso'] == [('Sistemas', 3)]


@pytest.mark.django_db
def test_indicadores_sem_turmas_nao_dividem_por_zero(db):
    dados = get_indicadores_gerenciais()

    assert dados['totais'] == {
        'turmas': 0, 'matriculas': 0, 'vagas': 0, 'ocupacao': 0,
        'em_risco': 0, 'taxa_aprovacao': None, 'concluidos': 0,
    }


@pytest.mark.django_db
def test_pendencias_contam_transferencias_e_aproveitamentos(cenario, user_secretaria):
    aluno = cenario['alunos'][0]
    solicitar_transferencia(
        usuario=user_secretaria, aluno=aluno, curso=cenario['si'], tipo='ENTRADA',
        instituicao_externa='UFX', curso_externo='Computação', data_referencia=date(2026, 8, 1),
        documentos='Histórico entregue.',
    )
    registrar_aproveitamento(
        usuario=user_secretaria, aluno=aluno, disciplina=cenario['algoritmos'],
        instituicao_origem='UFX', disciplina_origem='Programação', carga_horaria_origem=80,
    )

    assert get_indicadores_gerenciais()['pendencias'] == {'transferencias': 1, 'aproveitamentos': 1}
    assert get_indicadores_gerenciais(curso_id=cenario['direito'].pk)['pendencias'] == {
        'transferencias': 0, 'aproveitamentos': 0,
    }


@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_coordenacao', 'user_secretaria'])
def test_painel_disponivel_para_coordenacao_e_secretaria(client, request, fixture, cenario):
    client.force_login(request.getfixturevalue(fixture))

    resposta = client.get(reverse('academics:painel_gerencial'))

    assert resposta.status_code == 200
    conteudo = resposta.content.decode()
    assert 'Painel gerencial' in conteudo
    assert 'Algoritmos' in conteudo


@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_aluno', 'user_professor'])
def test_painel_negado_para_aluno_e_professor(client, request, fixture):
    client.force_login(request.getfixturevalue(fixture))

    assert client.get(reverse('academics:painel_gerencial')).status_code == 403


@pytest.mark.django_db
def test_painel_exige_login(client):
    resposta = client.get(reverse('academics:painel_gerencial'))

    assert resposta.status_code == 302
    assert reverse('accounts:login') in resposta.url


@pytest.mark.django_db
def test_painel_filtro_invalido_retorna_400_sem_quebrar(client, user_coordenacao, cenario):
    client.force_login(user_coordenacao)

    resposta = client.get(reverse('academics:painel_gerencial'), {'curso': 'abc'})

    assert resposta.status_code == 400
    assert 'Filtros inválidos' in resposta.content.decode()


@pytest.mark.django_db
def test_painel_nao_expoe_nomes_de_alunos(client, user_secretaria, cenario):
    client.force_login(user_secretaria)

    conteudo = client.get(reverse('academics:painel_gerencial')).content.decode()

    assert all(aluno.full_name not in conteudo for aluno in cenario['alunos'])
