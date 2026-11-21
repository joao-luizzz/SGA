from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser
from assessments.models import Nota
from assessments.services import lancar_notas_em_lote
from attendance.models import Falta
from attendance.services import registrar_chamada
from communications.models import Comunicado
from communications.services import publicar_comunicado, atualizar_comunicado, inativar_comunicado
from enrollment.models import Matricula
from notifications.models import Notificacao, TipoNotificacao
from notifications.selectors import listar_notificacoes, contar_nao_lidas
from notifications.services import (
    notificar_evento_academico, sincronizar_comunicados, marcar_como_lida,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def turma(user_aluno, user_professor):
    curso = Curso.objects.create(nome='ADS', codigo='ADS-NOT')
    disciplina = Disciplina.objects.create(nome='Software', codigo='SW-NOT', carga_horaria=80, curso=curso)
    turma = Turma.objects.create(disciplina=disciplina, professor=user_professor,
                                 periodo_letivo='2026/2', vagas_maximas=30)
    Matricula.objects.create(aluno=user_aluno, turma=turma)
    return turma


def aviso(user, **kwargs):
    return Notificacao.objects.create(destinatario=user, titulo='Aviso pessoal', mensagem='Mensagem',
                                     tipo=TipoNotificacao.NOTA, **kwargs)


def publicar(autor, **kwargs):
    return publicar_comunicado(autor=autor, titulo='Novo comunicado', conteudo='Conteúdo',
                               escopo=kwargs.pop('escopo', 'GERAL'), **kwargs)


@pytest.mark.parametrize('fixture', ['user_aluno', 'user_professor', 'user_secretaria', 'user_coordenacao'])
def test_central_personal_all_roles(client, request, fixture, user_inactive):
    user = request.getfixturevalue(fixture)
    own = aviso(user)
    foreign = aviso(user_inactive)
    client.force_login(user)
    response = client.get(reverse('notifications:central'))
    assert response.status_code == 200
    assert list(response.context['page_obj']) == [own]
    assert response.context['notificacoes_nao_lidas'] == 1
    for name in ['detalhe', 'ler']:
        url = reverse('notifications:' + name, args=[foreign.pk])
        assert (client.get(url) if name == 'detalhe' else client.post(url)).status_code == 404
    foreign.refresh_from_db()
    assert not foreign.lida


def test_superuser_personal_central_has_no_bypass(client, user_aluno, user_secretaria):
    user_secretaria.is_superuser = True
    user_secretaria.save()
    foreign = aviso(user_aluno)
    client.force_login(user_secretaria)
    assert client.get(reverse('notifications:detalhe', args=[foreign.pk])).status_code == 404
    assert client.post(reverse('notifications:ler', args=[foreign.pk])).status_code == 404
    assert not listar_notificacoes(user_secretaria).exists()


def test_read_and_all_read_idempotent(client, user_aluno, user_professor):
    own = aviso(user_aluno)
    another = aviso(user_aluno)
    foreign = aviso(user_professor)
    client.force_login(user_aluno)
    detail = reverse('notifications:detalhe', args=[own.pk])
    assert client.get(detail).status_code == 200
    own.refresh_from_db()
    assert not own.lida  # GET nunca muda estado.
    read = reverse('notifications:ler', args=[own.pk])
    assert client.get(read).status_code == 405
    assert client.post(read).status_code == 302
    own.refresh_from_db()
    read_at = own.lida_em
    client.post(read)
    own.refresh_from_db()
    assert own.lida_em == read_at
    assert contar_nao_lidas(user_aluno) == 1
    assert client.get(detail).status_code == 200
    all_read = reverse('notifications:ler_todas')
    assert client.get(all_read).status_code == 405
    assert client.post(all_read).status_code == 302
    another.refresh_from_db()
    foreign.refresh_from_db()
    assert another.lida and not foreign.lida
    assert contar_nao_lidas(user_aluno) == 0


def test_pagination_counter_and_escaping(client, user_aluno):
    for _ in range(23):
        aviso(user_aluno)
    latest = aviso(user_aluno)
    latest.titulo = '<script>alert(1)</script>'
    latest.save()
    client.force_login(user_aluno)
    response = client.get(reverse('notifications:central'))
    assert len(response.context['page_obj']) == 20
    assert response.context['notificacoes_nao_lidas'] == 24
    assert b'&lt;script&gt;' in response.content
    assert b'<script>alert(1)</script>' not in response.content
    page2 = client.get(reverse('notifications:central'), {'page': 2})
    assert len(page2.context['page_obj']) == 4
    assert client.get(reverse('notifications:central'), {'page': 'invalid'}).status_code == 200


def test_anonymous_inactive_and_missing_id(client, user_aluno, user_inactive):
    own = aviso(user_aluno)
    assert client.get(reverse('notifications:central')).status_code == 302
    assert client.post(reverse('notifications:ler_todas')).status_code == 302
    assert not listar_notificacoes(AnonymousUser()).exists()
    assert not listar_notificacoes(None).exists()
    assert not listar_notificacoes(user_inactive).exists()
    assert notificar_evento_academico(destinatario=user_inactive, tipo=TipoNotificacao.NOTA) is None
    client.force_login(user_aluno)
    assert client.get(reverse('notifications:detalhe', args=[own.pk + 99])).status_code == 404


def test_csrf_read_one_and_all(user_aluno):
    own = aviso(user_aluno)
    client = Client(enforce_csrf_checks=True)
    client.force_login(user_aluno)
    for url in [reverse('notifications:ler', args=[own.pk]), reverse('notifications:ler_todas')]:
        assert client.post(url).status_code == 403
        client.get(reverse('notifications:central'))
        assert client.post(url, {'csrfmiddlewaretoken': client.cookies['csrftoken'].value}).status_code == 302


def test_communications_reuse_visibility_and_no_duplicate(user_secretaria, user_aluno, user_professor, client):
    comunicado = publicar(user_secretaria, escopo='PAPEL', papel_destino='ALUNO')
    assert Notificacao.objects.filter(destinatario=user_aluno, comunicado=comunicado).count() == 1
    assert not Notificacao.objects.filter(destinatario=user_professor).exists()
    assert Notificacao.objects.filter(destinatario=user_secretaria).exists()  # já permitido no mural
    sincronizar_comunicados(user_aluno)
    atualizar_comunicado(comunicado=comunicado, autor=user_secretaria, titulo=comunicado.titulo,
                          conteudo=comunicado.conteudo, escopo='PAPEL', papel_destino='ALUNO')
    assert Notificacao.objects.filter(destinatario=user_aluno).count() == 1
    client.force_login(user_aluno)
    own = Notificacao.objects.get(destinatario=user_aluno)
    assert client.get(reverse('notifications:detalhe', args=[own.pk])).status_code == 200
    inativar_comunicado(comunicado=comunicado, autor=user_secretaria)
    assert contar_nao_lidas(user_aluno) == 0
    assert client.get(reverse('notifications:detalhe', args=[own.pk])).status_code == 404
    assert client.post(reverse('notifications:ler', args=[own.pk])).status_code == 404


def test_scheduled_comms_only_after_publication(user_secretaria, user_aluno):
    future = timezone.now() + timedelta(hours=1)
    comunicado = publicar(user_secretaria, publicar_em=future)
    assert not Notificacao.objects.exists()
    sincronizar_comunicados(user_aluno)
    assert not Notificacao.objects.exists()
    with patch('communications.selectors.timezone.now', return_value=future + timedelta(seconds=1)):
        sincronizar_comunicados(user_aluno)
        assert contar_nao_lidas(user_aluno) == 1
    assert Notificacao.objects.get().comunicado_id == comunicado.pk


def test_expired_and_revoked_scope_hidden(user_secretaria, user_aluno, user_professor):
    comunicado = publicar(user_secretaria)
    own = Notificacao.objects.get(destinatario=user_aluno)
    atualizar_comunicado(comunicado=comunicado, autor=user_secretaria, titulo='Restrito',
                         conteudo='Restrito', escopo='PAPEL', papel_destino='PROFESSOR')
    assert not listar_notificacoes(user_aluno).filter(pk=own.pk).exists()
    assert contar_nao_lidas(user_professor) == 1
    Comunicado.objects.filter(pk=comunicado.pk).update(expirar_em=timezone.now() - timedelta(seconds=1))
    assert contar_nao_lidas(user_professor) == 0


@pytest.mark.parametrize('event', ['comunicado', 'nota', 'frequencia'])
def test_three_events_rollback_and_effective_changes(event, turma, user_aluno, user_professor, user_secretaria):
    matricula = Matricula.objects.get(aluno=user_aluno)
    def action():
        if event == 'comunicado':
            return publicar(user_secretaria)
        if event == 'nota':
            return lancar_notas_em_lote(user_professor, turma, {matricula.pk: {'P1': 7}})
        return registrar_chamada(user_professor, turma, date(2026, 10, 8), {user_aluno.pk: True})
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            action()
            assert Notificacao.objects.filter(destinatario=user_aluno).exists()
            raise RuntimeError('rollback')
    assert not Notificacao.objects.exists()
    assert not Nota.objects.exists()
    assert not Falta.objects.exists()
    assert not Comunicado.objects.exists()
    action()
    assert Notificacao.objects.filter(destinatario=user_aluno).count() == 1
    if event != 'comunicado':
        action()  # mesmo lançamento não produz novo evento
        assert Notificacao.objects.filter(destinatario=user_aluno).count() == 1
        if event == 'nota':
            lancar_notas_em_lote(user_professor, turma, {matricula.pk: {'P1': 8}})
        else:
            registrar_chamada(user_professor, turma, date(2026, 10, 8), {user_aluno.pk: False})
        assert Notificacao.objects.filter(destinatario=user_aluno).count() == 2


def test_failed_grade_batch_rolls_back_notification(turma, user_aluno, user_professor):
    matricula = Matricula.objects.get(aluno=user_aluno)
    with pytest.raises(ValidationError):
        lancar_notas_em_lote(user_professor, turma, {matricula.pk: {'P1': 9, 'EXAME': 10}})
    assert not Notificacao.objects.exists()
    assert not Nota.objects.exists()


def test_failed_operations_do_not_notify(turma, user_aluno, user_professor, user_secretaria):
    with pytest.raises(ValidationError):
        registrar_chamada(user_professor, turma, date(2026, 10, 8), {})
    with pytest.raises(ValidationError):
        publicar(user_secretaria, expirar_em=timezone.now() - timedelta(days=1))
    assert not Notificacao.objects.exists()


def test_service_does_not_allow_foreign_mark(user_aluno, user_professor):
    from django.http import Http404
    own = aviso(user_aluno)
    with pytest.raises(Http404):
        marcar_como_lida(user_professor, own.pk)
    own.refresh_from_db()
    assert not own.lida


def test_three_events_http(client, turma, user_aluno, user_professor, user_secretaria):
    client.force_login(user_secretaria)
    response = client.post(reverse('communications:create'), {
        'titulo': 'Aviso HTTP', 'conteudo': 'Comunicado publicado', 'escopo': 'GERAL', 'ativo': 'on',
    })
    assert response.status_code == 302
    assert Notificacao.objects.filter(destinatario=user_aluno, tipo='COMUNICADO').count() == 1
    client.force_login(user_professor)
    matricula = Matricula.objects.get(aluno=user_aluno)
    response = client.post(reverse('assessments:turma_notas', args=[turma.pk]), {
        f'nota_{matricula.pk}_P1': '8.00',
    })
    assert response.status_code == 302
    assert Notificacao.objects.filter(destinatario=user_aluno, tipo='NOTA').count() == 1
    response = client.post(reverse('attendance:chamada_lancar'), {
        'step': '2', 'turma_id': turma.pk, 'data_aula': '2026-10-08', f'presente_{user_aluno.pk}': 'on',
    })
    assert response.status_code == 302
    assert Notificacao.objects.filter(destinatario=user_aluno, tipo='FREQUENCIA').count() == 1
    client.force_login(user_aluno)
    response = client.get(reverse('notifications:central'))
    assert response.context['notificacoes_nao_lidas'] == 3
    assert len(response.context['page_obj']) == 3


def test_unchanged_communication_does_not_emit(user_secretaria, user_aluno):
    # Registro anterior à entrega: não simular publicação ao salvar sem mudanças.
    comunicado = Comunicado.objects.create(autor=user_secretaria, titulo='Anterior', conteudo='Original', escopo='GERAL')
    atualizar_comunicado(comunicado=comunicado, autor=user_secretaria, titulo='Anterior', conteudo='Original', escopo='GERAL')
    assert not Notificacao.objects.exists()
