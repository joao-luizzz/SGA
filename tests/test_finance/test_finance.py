from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from academics.models import Curso, Disciplina, Turma
from academics.selectors import get_indicadores_gerenciais
from accounts.models import AcaoAuditoria, AuditoriaLog, CustomUser, UserRole
from enrollment.models import Matricula
from finance.models import Cobranca, StatusCobranca
from finance.selectors import listar_cobrancas, resumir_cobrancas
from finance.services import cancelar_cobranca, lancar_cobranca, registrar_pagamento


HOJE = timezone.localdate()


def _lancar(usuario, aluno, **extra):
    dados = dict(usuario=usuario, aluno=aluno, competencia='2026-11', descricao='Mensalidade',
                 valor=Decimal('450.00'), vencimento=HOJE + timedelta(days=10))
    dados.update(extra)
    return lancar_cobranca(**dados)


@pytest.fixture
def outro_aluno(db):
    return CustomUser.objects.create_user(email='outro@sga.edu.br', full_name='Outro Aluno',
                                          role=UserRole.ALUNO, password='x', must_change_password=False)


@pytest.fixture
def cobranca(user_secretaria, user_aluno):
    return _lancar(user_secretaria, user_aluno)


# --- Regras (RN24, RN25) ---------------------------------------------------

@pytest.mark.django_db
def test_lancar_cobranca_aberta_com_auditoria(cobranca, user_secretaria):
    assert cobranca.status == StatusCobranca.ABERTA
    assert not cobranca.em_atraso
    log = AuditoriaLog.objects.get(tabela_afetada='Cobranca', registro_id=cobranca.pk)
    assert log.acao == AcaoAuditoria.CRIAR
    assert '450.00' in log.valor_novo
    assert log.usuario == user_secretaria


@pytest.mark.django_db
def test_recusa_duplicada_mas_permite_apos_cancelamento(cobranca, user_secretaria, user_aluno):
    with pytest.raises(ValidationError, match='Já existe'):
        _lancar(user_secretaria, user_aluno, descricao='  Mensalidade ')

    cancelar_cobranca(usuario=user_secretaria, cobranca_id=cobranca.pk, justificativa='Lançada em duplicidade.')

    assert _lancar(user_secretaria, user_aluno).status == StatusCobranca.ABERTA


@pytest.mark.django_db
@pytest.mark.parametrize('campos, mensagem', [
    ({'valor': Decimal('0')}, 'valor'),
    ({'competencia': '2026-13'}, 'AAAA-MM'),
])
def test_valida_valor_e_competencia(user_secretaria, user_aluno, campos, mensagem):
    with pytest.raises(ValidationError, match=mensagem):
        _lancar(user_secretaria, user_aluno, **campos)


@pytest.mark.django_db
def test_recusa_aluno_inativo(user_secretaria, user_aluno):
    user_aluno.is_active = False
    user_aluno.save(update_fields=['is_active'])

    with pytest.raises(ValidationError, match='aluno ativo'):
        _lancar(user_secretaria, user_aluno)


@pytest.mark.django_db
def test_pagamento_registra_baixa_e_auditoria(cobranca, user_secretaria):
    paga = registrar_pagamento(usuario=user_secretaria, cobranca_id=cobranca.pk)

    assert paga.status == StatusCobranca.PAGA and paga.pago_em is not None
    log = AuditoriaLog.objects.get(tabela_afetada='Cobranca', acao=AcaoAuditoria.EDITAR)
    assert 'ABERTA' in log.valor_antigo and 'PAGA' in log.valor_novo


@pytest.mark.django_db
def test_estados_finais_nao_mudam(cobranca, user_secretaria):
    registrar_pagamento(usuario=user_secretaria, cobranca_id=cobranca.pk)

    with pytest.raises(ValidationError, match='abertas'):
        registrar_pagamento(usuario=user_secretaria, cobranca_id=cobranca.pk)
    with pytest.raises(ValidationError, match='abertas'):
        cancelar_cobranca(usuario=user_secretaria, cobranca_id=cobranca.pk, justificativa='Erro.')


@pytest.mark.django_db
@pytest.mark.parametrize('justificativa', ['', '  ', 'x' * 1001])
def test_cancelamento_exige_justificativa(cobranca, user_secretaria, justificativa):
    with pytest.raises(ValidationError, match='justificativa'):
        cancelar_cobranca(usuario=user_secretaria, cobranca_id=cobranca.pk, justificativa=justificativa)


@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_aluno', 'user_professor', 'user_coordenacao'])
def test_somente_secretaria_opera(request, fixture, cobranca, user_aluno):
    usuario = request.getfixturevalue(fixture)

    with pytest.raises(PermissionDenied):
        _lancar(usuario, user_aluno, descricao='Taxa')
    with pytest.raises(PermissionDenied):
        registrar_pagamento(usuario=usuario, cobranca_id=cobranca.pk)
    with pytest.raises(PermissionDenied):
        cancelar_cobranca(usuario=usuario, cobranca_id=cobranca.pk, justificativa='x')


@pytest.mark.django_db
def test_constraint_impede_paga_sem_data(user_secretaria, user_aluno):
    with pytest.raises(IntegrityError), transaction.atomic():
        Cobranca.objects.create(aluno=user_aluno, competencia='2026-11', descricao='X', valor=1,
                                vencimento=HOJE, status=StatusCobranca.PAGA, registrado_por=user_secretaria)


@pytest.mark.django_db
def test_atraso_e_resumo_derivados(user_secretaria, user_aluno):
    atrasada = _lancar(user_secretaria, user_aluno, descricao='Atrasada', vencimento=HOJE - timedelta(days=1))
    _lancar(user_secretaria, user_aluno, descricao='Futura', valor=Decimal('100.00'))
    paga = _lancar(user_secretaria, user_aluno, descricao='Paga', vencimento=HOJE - timedelta(days=5))
    registrar_pagamento(usuario=user_secretaria, cobranca_id=paga.pk)

    assert atrasada.em_atraso
    resumo = resumir_cobrancas(Cobranca.objects.all())
    assert resumo == {'total_aberto': Decimal('550.00'), 'quantidade_atraso': 1,
                      'total_atraso': Decimal('450.00')}
    assert list(listar_cobrancas(user_secretaria, status='ATRASO')) == [atrasada]


@pytest.mark.django_db
def test_aluno_lista_somente_as_proprias(cobranca, user_secretaria, user_aluno, outro_aluno):
    _lancar(user_secretaria, outro_aluno)

    assert list(listar_cobrancas(user_aluno)) == [cobranca]
    assert listar_cobrancas(user_secretaria).count() == 2


@pytest.mark.django_db
def test_painel_gerencial_mostra_cobrancas_em_atraso(user_secretaria, user_aluno, outro_aluno, user_professor):
    curso = Curso.objects.create(nome='Sistemas', codigo='SI')
    disciplina = Disciplina.objects.create(nome='Algoritmos', codigo='ALG', carga_horaria=60, curso=curso)
    turma = Turma.objects.create(disciplina=disciplina, periodo_letivo='2026/2', horarios='SEG 08:00-10:00',
                                 sala='A1', vagas_maximas=5, professor=user_professor)
    Matricula.objects.create(aluno=user_aluno, turma=turma)
    _lancar(user_secretaria, user_aluno, vencimento=HOJE - timedelta(days=3))
    _lancar(user_secretaria, outro_aluno, vencimento=HOJE - timedelta(days=3), valor=Decimal('99.90'))

    geral = get_indicadores_gerenciais()['pendencias']
    do_curso = get_indicadores_gerenciais(curso_id=curso.pk)['pendencias']

    assert (geral['cobrancas_atraso'], geral['valor_atraso']) == (2, Decimal('549.90'))
    assert (do_curso['cobrancas_atraso'], do_curso['valor_atraso']) == (1, Decimal('450.00'))


# --- Views e RBAC ------------------------------------------------------------

@pytest.mark.django_db
def test_secretaria_lanca_paga_e_cancela_pela_tela(client, user_secretaria, user_aluno):
    client.force_login(user_secretaria)

    resposta = client.post(reverse('finance:criar'), {
        'aluno': user_aluno.pk, 'competencia': '2026-11', 'descricao': 'Mensalidade',
        'valor': '450.00', 'vencimento': (HOJE + timedelta(days=5)).isoformat(),
    })
    primeira = Cobranca.objects.get()
    assert resposta.status_code == 302
    assert resposta.url == reverse('finance:detalhe', args=[primeira.pk])

    assert client.post(reverse('finance:pagar', args=[primeira.pk])).status_code == 302
    primeira.refresh_from_db()
    assert primeira.status == StatusCobranca.PAGA

    segunda = _lancar(user_secretaria, user_aluno, descricao='Taxa')
    invalido = client.post(reverse('finance:cancelar', args=[segunda.pk]), {'justificativa': ''})
    assert invalido.status_code == 400
    valido = client.post(reverse('finance:cancelar', args=[segunda.pk]), {'justificativa': 'Isenção aprovada.'})
    assert valido.status_code == 302
    segunda.refresh_from_db()
    assert segunda.status == StatusCobranca.CANCELADA


@pytest.mark.django_db
def test_aluno_ve_extrato_proprio_e_nao_opera(client, cobranca, user_aluno, user_secretaria, outro_aluno):
    alheia = _lancar(user_secretaria, outro_aluno)
    client.force_login(user_aluno)

    extrato = client.get(reverse('finance:index'))
    assert extrato.status_code == 200
    assert list(extrato.context['page_obj']) == [cobranca]
    assert client.get(reverse('finance:detalhe', args=[cobranca.pk])).status_code == 200
    assert client.get(reverse('finance:detalhe', args=[alheia.pk])).status_code == 404
    assert client.get(reverse('finance:criar')).status_code == 403
    assert client.post(reverse('finance:pagar', args=[cobranca.pk])).status_code == 403
    assert 'Registrar pagamento' not in client.get(reverse('finance:detalhe', args=[cobranca.pk])).content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize('fixture', ['user_professor', 'user_coordenacao'])
def test_professor_e_coordenacao_nao_acessam_financeiro(client, request, fixture):
    client.force_login(request.getfixturevalue(fixture))

    assert client.get(reverse('finance:index')).status_code == 403


@pytest.mark.django_db
def test_filtro_invalido_retorna_400(client, user_secretaria):
    client.force_login(user_secretaria)

    assert client.get(reverse('finance:index'), {'status': 'X'}).status_code == 400


@pytest.mark.django_db
def test_financeiro_nao_bloqueia_matricula(user_secretaria, user_aluno, user_professor):
    """D2: cobrança em atraso não impede matrícula."""
    from enrollment.services import matricular_aluno_administrativo

    curso = Curso.objects.create(nome='Sistemas', codigo='SI')
    disciplina = Disciplina.objects.create(nome='Algoritmos', codigo='ALG', carga_horaria=60, curso=curso)
    turma = Turma.objects.create(disciplina=disciplina, periodo_letivo='2026/2', horarios='SEG 08:00-10:00',
                                 sala='A1', vagas_maximas=5, professor=user_professor)
    _lancar(user_secretaria, user_aluno, vencimento=date(2026, 1, 10))

    assert matricular_aluno_administrativo(user_secretaria, user_aluno, turma)
