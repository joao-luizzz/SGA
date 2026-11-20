"""Critérios de aceite revisados na auditoria das issues (#43, #46, #57)."""
from datetime import time

import pytest
from django.urls import reverse

from academics.models import Curso, Disciplina, HorarioTurma, Turma
from communications.models import EscopoComunicado
from communications.services import publicar_comunicado
from enrollment.models import Matricula


@pytest.fixture
def estrutura(db, user_professor):
    si = Curso.objects.create(nome='Sistemas', codigo='SI')
    direito = Curso.objects.create(nome='Direito', codigo='DIR')
    algoritmos = Disciplina.objects.create(nome='Algoritmos', codigo='ALG', carga_horaria=60, curso=si)
    redes = Disciplina.objects.create(nome='Redes', codigo='RED', carga_horaria=60, curso=si)
    civil = Disciplina.objects.create(nome='Civil', codigo='CIV', carga_horaria=60, curso=direito)
    turmas = {}
    for chave, disciplina, dia in (('alg', algoritmos, 'SEG'), ('red', redes, 'TER'), ('civ', civil, 'QUA')):
        turma = Turma.objects.create(disciplina=disciplina, periodo_letivo='2026/2', horarios=f'{dia} 08:00-10:00',
                                     sala=f'S-{chave}', vagas_maximas=10, professor=user_professor)
        HorarioTurma.objects.create(turma=turma, dia_semana=dia, hora_inicio=time(8), hora_fim=time(10))
        turmas[chave] = turma
    inativa = Turma.objects.create(disciplina=algoritmos, periodo_letivo='2026/1', horarios='QUI 08:00-10:00',
                                   sala='S-x', vagas_maximas=10, professor=user_professor, ativo=False)
    HorarioTurma.objects.create(turma=inativa, dia_semana='QUI', hora_inicio=time(8), hora_fim=time(10))
    return {'si': si, 'direito': direito, 'turmas': turmas, 'inativa': inativa}


def _disciplinas_na_grade(resposta):
    return sorted({h.turma.disciplina.nome for _, horarios in resposta.context['grade_ordenada'] for h in horarios})


# --- #57: filtros por curso, turma e período ---------------------------------

@pytest.mark.django_db
def test_grade_filtra_por_turma(client, user_coordenacao, estrutura):
    client.force_login(user_coordenacao)

    resposta = client.get(reverse('academics:grade_horaria'), {'turma': estrutura['turmas']['red'].pk})

    assert resposta.status_code == 200
    assert _disciplinas_na_grade(resposta) == ['Redes']
    assert resposta.context['selected_turma'] == estrutura['turmas']['red'].pk


@pytest.mark.django_db
def test_grade_combina_curso_e_periodo(client, user_secretaria, estrutura):
    client.force_login(user_secretaria)

    resposta = client.get(reverse('academics:grade_horaria'), {'curso': estrutura['si'].pk, 'periodo': '2026/2'})

    assert _disciplinas_na_grade(resposta) == ['Algoritmos', 'Redes']


@pytest.mark.django_db
@pytest.mark.parametrize('parametro', ['curso', 'turma'])
def test_grade_ignora_id_invalido_sem_erro(client, user_coordenacao, estrutura, parametro):
    client.force_login(user_coordenacao)

    resposta = client.get(reverse('academics:grade_horaria'), {parametro: 'abc'})

    assert resposta.status_code == 200
    assert _disciplinas_na_grade(resposta) == ['Algoritmos', 'Civil', 'Redes']


# --- #46: vínculo da grade com a estrutura curricular ------------------------

@pytest.mark.django_db
def test_grade_respeita_vinculo_curso_disciplina_turma(client, user_coordenacao, estrutura):
    """O horário pertence à turma, que pertence à disciplina, que pertence ao curso."""
    client.force_login(user_coordenacao)

    resposta = client.get(reverse('academics:grade_horaria'), {'curso': estrutura['direito'].pk})

    horarios = [h for _, lista in resposta.context['grade_ordenada'] for h in lista]
    assert [h.turma.disciplina.curso for h in horarios] == [estrutura['direito']]


@pytest.mark.django_db
def test_grade_exclui_turma_inativa_e_aluno_ve_so_a_propria(client, user_aluno, estrutura):
    Matricula.objects.create(aluno=user_aluno, turma=estrutura['turmas']['alg'])
    client.force_login(user_aluno)

    resposta = client.get(reverse('academics:grade_horaria'))

    assert _disciplinas_na_grade(resposta) == ['Algoritmos']
    assert all(h.turma.ativo for _, lista in resposta.context['grade_ordenada'] for h in lista)


# --- #43: comunicados relevantes no painel -----------------------------------

@pytest.mark.django_db
def test_painel_do_aluno_mostra_somente_comunicados_do_proprio_publico(
    client, user_aluno, user_secretaria, user_coordenacao, estrutura,
):
    Matricula.objects.create(aluno=user_aluno, turma=estrutura['turmas']['alg'])
    publicar_comunicado(autor=user_secretaria, titulo='Aviso geral', conteudo='Para todos.',
                        escopo=EscopoComunicado.GERAL)
    publicar_comunicado(autor=user_coordenacao, titulo='Aviso de Civil', conteudo='Só Civil.',
                        escopo=EscopoComunicado.TURMA, turma=estrutura['turmas']['civ'])
    client.force_login(user_aluno)

    conteudo = client.get(reverse('accounts:dashboard_aluno')).content.decode()

    assert 'Comunicados recentes' in conteudo
    assert 'Aviso geral' in conteudo
    assert 'Aviso de Civil' not in conteudo


@pytest.mark.django_db
@pytest.mark.parametrize('fixture, rota', [
    ('user_professor', 'accounts:dashboard_professor'),
    ('user_secretaria', 'accounts:dashboard_secretaria'),
    ('user_coordenacao', 'accounts:dashboard_coordenacao'),
])
def test_todos_os_paineis_exibem_comunicados(client, request, user_secretaria, fixture, rota):
    for indice in range(5):
        publicar_comunicado(autor=user_secretaria, titulo=f'Aviso {indice}', conteudo='x',
                            escopo=EscopoComunicado.GERAL)
    client.force_login(request.getfixturevalue(fixture))

    resposta = client.get(reverse(rota))

    assert resposta.status_code == 200
    assert len(resposta.context['comunicados_recentes']) == 3
    assert 'Aviso 4' in resposta.content.decode()


@pytest.mark.django_db
def test_painel_sem_comunicados_mostra_estado_vazio(client, user_aluno):
    client.force_login(user_aluno)

    conteudo = client.get(reverse('accounts:dashboard_aluno')).content.decode()

    assert 'Nenhum comunicado vigente para você.' in conteudo


@pytest.mark.django_db
def test_opcoes_de_turma_acompanham_o_filtro_de_curso(client, user_coordenacao, estrutura):
    client.force_login(user_coordenacao)

    resposta = client.get(reverse('academics:grade_horaria'), {'curso': estrutura['direito'].pk})

    assert [t.disciplina.nome for t in resposta.context['turmas']] == ['Civil']
