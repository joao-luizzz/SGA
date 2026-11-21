"""Público em lote dos comunicados e contador sem escrita (ressalvas da revisão da PR #73)."""
from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from communications.models import Comunicado, EscopoComunicado
from communications.selectors import listar_comunicados_para_usuario, listar_destinatarios_comunicado
from enrollment.models import Matricula, StatusMatricula
from notifications.models import Notificacao
from notifications.selectors import contar_nao_lidas
from notifications.services import notificar_comunicado

pytestmark = pytest.mark.django_db


def _usuario(email, role, **extra):
    return CustomUser.objects.create_user(email=email, full_name=email.split('@')[0], role=role,
                                          password='x', must_change_password=False, **extra)


@pytest.fixture
def universo(user_secretaria):
    """Usuários de todos os papéis com vínculos variados em dois cursos."""
    si = Curso.objects.create(nome='Sistemas', codigo='SI')
    direito = Curso.objects.create(nome='Direito', codigo='DIR')
    alg = Disciplina.objects.create(nome='Algoritmos', codigo='ALG', carga_horaria=60, curso=si)
    civ = Disciplina.objects.create(nome='Civil', codigo='CIV', carga_horaria=60, curso=direito)
    prof_si = _usuario('prof.si@sga.edu.br', UserRole.PROFESSOR)
    prof_dir = _usuario('prof.dir@sga.edu.br', UserRole.PROFESSOR)
    prof_inativa = _usuario('prof.inativa@sga.edu.br', UserRole.PROFESSOR)
    turma_si = Turma.objects.create(disciplina=alg, periodo_letivo='2026/2', horarios='SEG 08:00-10:00',
                                    vagas_maximas=10, professor=prof_si)
    turma_dir = Turma.objects.create(disciplina=civ, periodo_letivo='2026/2', horarios='TER 08:00-10:00',
                                     vagas_maximas=10, professor=prof_dir)
    Turma.objects.create(disciplina=alg, periodo_letivo='2025/1', horarios='QUA 08:00-10:00',
                         vagas_maximas=10, professor=prof_inativa, ativo=False)
    aluno_si = _usuario('aluno.si@sga.edu.br', UserRole.ALUNO)
    aluno_dir = _usuario('aluno.dir@sga.edu.br', UserRole.ALUNO)
    aluno_trancado = _usuario('aluno.trancado@sga.edu.br', UserRole.ALUNO)
    _usuario('aluno.sem@sga.edu.br', UserRole.ALUNO)
    _usuario('aluno.inativo@sga.edu.br', UserRole.ALUNO, is_active=False)
    _usuario('coord@sga.edu.br', UserRole.COORDENACAO)
    _usuario('super@sga.edu.br', UserRole.ALUNO, is_superuser=True)
    Matricula.objects.create(aluno=aluno_si, turma=turma_si)
    Matricula.objects.create(aluno=aluno_dir, turma=turma_dir)
    Matricula.objects.create(aluno=aluno_trancado, turma=turma_si, status=StatusMatricula.TRANCADA)
    return {'si': si, 'turma_si': turma_si, 'autor': user_secretaria}


def _comunicados(universo):
    base = dict(titulo='Aviso', conteudo='x', autor=universo['autor'])
    agora = timezone.now()
    return [
        Comunicado.objects.create(escopo=EscopoComunicado.GERAL, **base),
        Comunicado.objects.create(escopo=EscopoComunicado.PAPEL, papel_destino='ALUNO', **base),
        Comunicado.objects.create(escopo=EscopoComunicado.PAPEL, papel_destino='PROFESSOR', **base),
        Comunicado.objects.create(escopo=EscopoComunicado.PAPEL, papel_destino='SECRETARIA', **base),
        Comunicado.objects.create(escopo=EscopoComunicado.TURMA, turma=universo['turma_si'], **base),
        Comunicado.objects.create(escopo=EscopoComunicado.CURSO, curso=universo['si'], **base),
        Comunicado.objects.create(escopo=EscopoComunicado.GERAL, publicar_em=agora + timedelta(hours=1), **base),
        Comunicado.objects.create(escopo=EscopoComunicado.GERAL, expirar_em=agora - timedelta(minutes=1),
                                  publicar_em=agora - timedelta(hours=1), **base),
        Comunicado.objects.create(escopo=EscopoComunicado.GERAL, ativo=False, **base),
    ]


def test_publico_em_lote_equivale_ao_mural_para_todos_os_usuarios(universo):
    usuarios = list(CustomUser.objects.filter(is_active=True))
    for comunicado in _comunicados(universo):
        esperado = {u.pk for u in usuarios
                    if listar_comunicados_para_usuario(u).filter(pk=comunicado.pk).exists()}
        obtido = set(listar_destinatarios_comunicado(comunicado).values_list('pk', flat=True))
        assert obtido == esperado, (comunicado.escopo, comunicado.papel_destino)


def test_publicacao_usa_numero_de_consultas_constante(universo):
    comunicado = Comunicado.objects.create(escopo=EscopoComunicado.GERAL, titulo='Aviso', conteudo='x',
                                           autor=universo['autor'])
    with CaptureQueriesContext(connection) as poucos:
        notificar_comunicado(comunicado)
    for indice in range(15):
        _usuario(f'extra{indice}@sga.edu.br', UserRole.ALUNO)
    outro = Comunicado.objects.create(escopo=EscopoComunicado.GERAL, titulo='Outro', conteudo='x',
                                      autor=universo['autor'])
    with CaptureQueriesContext(connection) as muitos:
        notificar_comunicado(outro)

    assert len(muitos) == len(poucos)
    assert Notificacao.objects.filter(comunicado=outro).count() == CustomUser.objects.filter(is_active=True).count()


def test_publicacao_repetida_nao_duplica(universo):
    comunicado = Comunicado.objects.create(escopo=EscopoComunicado.TURMA, turma=universo['turma_si'],
                                           titulo='Aviso', conteudo='x', autor=universo['autor'])
    notificar_comunicado(comunicado)
    total = Notificacao.objects.count()

    notificar_comunicado(comunicado)

    assert Notificacao.objects.count() == total


def test_contador_inclui_pendentes_sem_escrever_no_banco(client, user_aluno, user_secretaria):
    Comunicado.objects.create(escopo=EscopoComunicado.GERAL, titulo='Sem materializar', conteudo='x',
                              autor=user_secretaria)
    client.force_login(user_aluno)

    with CaptureQueriesContext(connection) as consultas:
        resposta = client.get(reverse('accounts:dashboard_aluno'))

    assert resposta.context['notificacoes_nao_lidas'] == 1
    assert contar_nao_lidas(user_aluno) == 1
    assert not Notificacao.objects.exists()
    escritas = [q['sql'] for q in consultas.captured_queries
                if q['sql'].lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE'))
                and 'notifications_notificacao' in q['sql']]
    assert escritas == []

    client.get(reverse('notifications:central'))
    assert Notificacao.objects.filter(destinatario=user_aluno).count() == 1
    assert contar_nao_lidas(user_aluno) == 1
