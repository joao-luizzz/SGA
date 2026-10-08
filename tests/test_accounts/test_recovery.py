import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.db import close_old_connections, connection
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.logging import RecoveryLogFilter
from accounts.models import AuditoriaLog

pytestmark = pytest.mark.django_db
NEW_PASSWORD = 'NovaSenhaSegura456!'


@pytest.fixture(autouse=True)
def recovery_settings(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 0
    settings.PASSWORD_RESET_IP_COOLDOWN = 0
    cache.clear()


def link(user, token=None):
    return reverse('accounts:password_reset_confirm', kwargs={
        'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': token or default_token_generator.make_token(user),
    })


def confirm(client, url, password=NEW_PASSWORD):
    response = client.get(url)
    assert response.status_code == 302
    assert 'set-password' in response.url
    return client.post(response.url, {'new_password1': password, 'new_password2': password})


def test_request_equivalent_and_full_http_reset(client, user_aluno, password, caplog):
    url = reverse('accounts:password_reset')
    existing = client.post(url, {'email': user_aluno.email}, follow=True)
    assert len(mail.outbox) == 1
    absent = client.post(url, {'email': 'naoexiste@sga.edu.br'}, follow=True)
    assert existing.status_code == absent.status_code == 200
    assert existing.redirect_chain == absent.redirect_chain
    assert existing.content == absent.content
    assert len(mail.outbox) == 1
    reset_url = re.search(r'http://localhost:8000([^\s]+)', mail.outbox[0].body).group(1)
    token = reset_url.rstrip('/').split('/')[-1]
    caplog.set_level(logging.DEBUG)
    assert confirm(client, reset_url).url == reverse('accounts:password_reset_complete')
    user_aluno.refresh_from_db()
    assert user_aluno.check_password(NEW_PASSWORD)
    assert not user_aluno.check_password(password)
    assert user_aluno.password != NEW_PASSWORD
    assert client.post(reverse('accounts:login'), {'username': user_aluno.email, 'password': password}).status_code == 200
    assert client.post(reverse('accounts:login'), {'username': user_aluno.email, 'password': NEW_PASSWORD}).status_code == 302
    assert not client.get(reset_url).context['validlink']
    log = AuditoriaLog.objects.get(tabela_afetada='CustomUser')
    assert log.valor_novo == 'Senha redefinida por recuperação.'
    for secret in (token, NEW_PASSWORD, password, user_aluno.password):
        assert secret not in caplog.text
        assert secret not in (log.valor_novo or '')


@pytest.mark.parametrize('case', ['invalid', 'expired', 'other_user', 'inactive', 'unusable'])
def test_invalid_links_do_not_change_password(client, user_aluno, user_professor, case, settings):
    token = default_token_generator.make_token(user_aluno)
    if case == 'invalid':
        token += 'bad'
    elif case == 'expired':
        settings.PASSWORD_RESET_TIMEOUT = 60
        with patch.object(default_token_generator, '_now', return_value=datetime.now() - timedelta(seconds=61)):
            token = default_token_generator.make_token(user_aluno)
    elif case == 'inactive':
        user_aluno.is_active = False
        user_aluno.save()
    elif case == 'unusable':
        user_aluno.set_unusable_password()
        user_aluno.save()
    url = link(user_professor if case == 'other_user' else user_aluno, token)
    response = client.get(url)
    # A token can still be cryptographically valid after account deactivation;
    # the locked service must reject its POST as well.
    if response.status_code == 302:
        response = client.post(response.url, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD})
    assert response.status_code == 200
    assert not AuditoriaLog.objects.filter(tabela_afetada='CustomUser').exists()
    user_aluno.refresh_from_db()
    assert not user_aluno.check_password(NEW_PASSWORD)
    user_professor.refresh_from_db()
    assert not user_professor.check_password(NEW_PASSWORD)


@pytest.mark.parametrize('candidate', ['123', '123456789', 'password', 'aluno@sga.edu.br'])
def test_password_validators_http(client, user_aluno, candidate):
    response = confirm(client, link(user_aluno), candidate)
    assert response.status_code == 200
    assert response.context['form'].errors
    user_aluno.refresh_from_db()
    assert not user_aluno.check_password(candidate)


def test_two_sessions_cannot_reuse_token(client, user_aluno):
    url = link(user_aluno)
    second = Client()
    first_url = client.get(url).url
    second_url = second.get(url).url
    data = {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD}
    assert client.post(first_url, data).status_code == 302
    assert second.post(second_url, data).status_code == 200
    assert AuditoriaLog.objects.filter(tabela_afetada='CustomUser').count() == 1


@pytest.mark.parametrize('fixture', ['user_inactive', 'user_aluno'])
def test_ineligible_accounts_neutral(client, request, fixture):
    user = request.getfixturevalue(fixture)
    if fixture == 'user_aluno':
        user.set_unusable_password()
        user.save()
    response = client.post(reverse('accounts:password_reset'), {'email': user.email}, follow=True)
    assert response.status_code == 200
    assert not mail.outbox
    assert b'conta eleg' in response.content


def test_reset_clears_initial_password_and_does_not_autologin(client, user_must_change_pw):
    assert confirm(client, link(user_must_change_pw)).status_code == 302
    user_must_change_pw.refresh_from_db()
    assert not user_must_change_pw.must_change_password
    assert '_auth_user_id' not in client.session


def test_csrf_for_both_forms(user_aluno):
    client = Client(enforce_csrf_checks=True)
    url = reverse('accounts:password_reset')
    assert client.post(url, {'email': user_aluno.email}).status_code == 403
    assert client.get(url).status_code == 200
    response = client.post(url, {'email': user_aluno.email, 'csrfmiddlewaretoken': client.cookies['csrftoken'].value})
    assert response.status_code == 302
    target = client.get(link(user_aluno)).url
    assert client.post(target, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD}).status_code == 403
    client.get(target)
    assert client.post(target, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD,
                               'csrfmiddlewaretoken': client.cookies['csrftoken'].value}).status_code == 302


def test_throttling_and_trusted_email_domain(client, user_aluno, settings):
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 60
    settings.PASSWORD_RESET_IP_COOLDOWN = 10
    settings.PASSWORD_RESET_DOMAIN = 'sga.example.edu'
    settings.PASSWORD_RESET_USE_HTTPS = True
    url = reverse('accounts:password_reset')
    first = client.post(url, {'email': user_aluno.email})
    second = client.post(url, {'email': user_aluno.email})
    assert first.url == second.url
    assert len(mail.outbox) == 1
    assert 'https://sga.example.edu/' in mail.outbox[0].body


def test_delivery_failure_sanitized(client, user_aluno, caplog):
    from smtplib import SMTPException
    with patch('accounts.forms.EmailMultiAlternatives.send', side_effect=SMTPException('secret-token secret-password')):
        response = client.post(reverse('accounts:password_reset'), {'email': user_aluno.email})
    assert response.status_code == 302
    assert 'secret-token' not in caplog.text
    assert 'secret-password' not in caplog.text
    assert 'Falha na entrega' in caplog.text


def test_server_logging_redacts_link():
    record = logging.LogRecord('django.server', logging.INFO, '', 1, 'GET %s',
                               ('/accounts/reset/MQ/abc-secret-token/',), None)
    assert RecoveryLogFilter().filter(record)
    assert 'abc-secret-token' not in record.getMessage()
    assert 'MQ' not in record.getMessage()


def test_referrer_policy_and_no_cache(client, user_aluno):
    response = client.get(link(user_aluno))
    assert response['Referrer-Policy'] == 'no-referrer'
    assert 'no-store' in response['Cache-Control']


@pytest.mark.django_db(transaction=True)
def test_concurrent_token_http(user_aluno):
    if connection.vendor != 'postgresql':
        pytest.skip('Bloqueio concorrente de recuperação exige PostgreSQL.')
    url = link(user_aluno)
    clients = [Client(), Client()]
    targets = [client.get(url).url for client in clients]
    barrier = Barrier(2)
    from accounts.recovery import redefinir_senha

    def simultaneous(*args, **kwargs):
        barrier.wait(timeout=10)
        return redefinir_senha(*args, **kwargs)

    def worker(index):
        close_old_connections()
        try:
            password = NEW_PASSWORD + str(index)
            return clients[index].post(targets[index], {
                'new_password1': password, 'new_password2': password,
            }).status_code
        finally:
            close_old_connections()

    with patch('accounts.recovery.redefinir_senha', side_effect=simultaneous):
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(worker, [0, 1]))
    assert sorted(statuses) == [200, 302]
    assert AuditoriaLog.objects.filter(tabela_afetada='CustomUser').count() == 1


@pytest.mark.parametrize('backend', ['console', 'filebased'])
def test_unsafe_backend_cannot_expose_recovery_link(client, user_aluno, settings, capsys, caplog, backend):
    settings.EMAIL_BACKEND = f'django.core.mail.backends.{backend}.EmailBackend'
    response = client.post(reverse('accounts:password_reset'), {'email': user_aluno.email})
    assert response.status_code == 302
    assert '/accounts/reset/' not in capsys.readouterr().out
    assert '/accounts/reset/' not in caplog.text
    assert 'envio bloqueado' in caplog.text


def test_ip_cooldown_and_invalid_email(client, user_aluno, user_professor, settings):
    settings.PASSWORD_RESET_IP_COOLDOWN = 60
    url = reverse('accounts:password_reset')
    assert client.post(url, {'email': 'inválido'}).status_code == 200
    assert client.post(url, {'email': user_aluno.email}).status_code == 302
    assert client.post(url, {'email': user_professor.email}).status_code == 302
    assert len(mail.outbox) == 1


def test_password_mismatch_and_malformed_uid(client, user_aluno):
    target = client.get(link(user_aluno)).url
    response = client.post(target, {'new_password1': NEW_PASSWORD, 'new_password2': NEW_PASSWORD + 'x'})
    assert response.status_code == 200
    assert response.context['form'].errors
    assert not client.get('/accounts/reset/invalid/token/').context['validlink']


def test_service_rechecks_validators_and_deleted_user(user_aluno):
    from accounts.services import redefinir_senha
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        redefinir_senha(user_id=user_aluno.pk, token=default_token_generator.make_token(user_aluno), password='123')
    with pytest.raises(ValidationError):
        redefinir_senha(user_id=user_aluno.pk + 100, token='invalid', password=NEW_PASSWORD)
    assert not AuditoriaLog.objects.exists()
