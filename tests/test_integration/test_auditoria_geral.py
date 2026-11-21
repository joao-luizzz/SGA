"""Problemas encontrados na auditoria geral antes do merge em main."""
from datetime import date, time, timedelta
from decimal import Decimal
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from academics.models import Curso, Disciplina, HorarioTurma, Turma
from academics.services import adicionar_pre_requisito, identificar_risco_academico, inativar_turma
from accounts.models import CustomUser, UserRole
from assessments.models import TipoAvaliacao as T
from assessments.selectors import SituacaoAcademica, calcular_resultado_academico
from attendance.services import registrar_chamada
from enrollment.models import Matricula, StatusMatricula
from enrollment.services import matricular_aluno_administrativo
from materials.models import MaterialAcademico

SEM_AULAS = {'total_aulas': 0, 'presencas': 0, 'faltas': 0, 'percentual': Decimal('100.0'), 'situacao': ''}


@pytest.fixture
def turma(db, user_professor):
    curso = Curso.objects.create(nome='Sistemas', codigo='SI')
    disciplina = Disciplina.objects.create(nome='Algoritmos', codigo='ALG', carga_horaria=60, curso=curso)
    return Turma.objects.create(disciplina=disciplina, periodo_letivo='2026/2', horarios='SEG 08:00-10:00',
                                sala='A1', vagas_maximas=10, professor=user_professor)


def _resultado(p1, p2, trabalho, exame=None):
    notas = {T.P1: Decimal(p1), T.P2: Decimal(p2), T.TRABALHO: Decimal(trabalho)}
    if exame is not None:
        notas[T.EXAME] = Decimal(exame)
    with patch('assessments.selectors.get_frequencia_do_aluno_na_turma', return_value=SEM_AULAS):
        return calcular_resultado_academico(SimpleNamespace(aluno=None, turma=None), notas)


# --- 1. Regra exata nas fronteiras (opção A) ---------------------------------

@pytest.mark.parametrize('notas, situacao, mp_exibida, mf_exibida', [
    (('6.00', '6.00', '5.99', None), SituacaoAcademica.ELEGIVEL_EXAME, '6.00', None),   # MP 5,9967
    (('4.00', '4.00', '3.99', None), SituacaoAcademica.REPROVADO_NOTA, '4.00', None),   # MP 3,9967
    (('5.00', '5.00', '5.00', '6.99'), SituacaoAcademica.REPROVADO_NOTA, '5.00', '6.00'),  # MF 5,995
    (('6.00', '6.00', '6.00', None), SituacaoAcademica.APROVADO_DIRETO, '6.00', None),
    (('4.00', '4.00', '4.00', None), SituacaoAcademica.ELEGIVEL_EXAME, '4.00', None),
    (('5.00', '5.00', '5.00', '7.00'), SituacaoAcademica.APROVADO_EXAME, '5.00', '6.00'),
    (('5.01', '5.01', '5.01', '6.99'), SituacaoAcademica.APROVADO_EXAME, '5.01', '6.00'),  # MF exatamente 6
])
def test_situacao_compara_media_exata_e_exibe_arredondada(notas, situacao, mp_exibida, mf_exibida):
    resultado = _resultado(*notas)

    assert resultado['situacao'] == situacao
    assert resultado['media_parcial'] == Decimal(mp_exibida)
    assert resultado['media_final'] == (Decimal(mf_exibida) if mf_exibida else None)


def test_risco_usa_a_media_exata():
    resultado = _resultado('6.00', '6.00', '5.99')
    notas = {T.P1: Decimal('6'), T.P2: Decimal('6'), T.TRABALHO: Decimal('5.99')}

    risco = identificar_risco_academico(notas=notas, resultado=resultado)

    assert risco['em_risco']


# --- 2. Seed cria a grade horária estruturada --------------------------------

@pytest.mark.django_db
def test_seed_cria_horarios_estruturados_e_grade_nao_fica_vazia(client):
    call_command('seed_demo', stdout=StringIO())
    call_command('seed_demo', stdout=StringIO())

    for turma in Turma.objects.filter(disciplina__codigo__in=['ES-DEMO', 'BD-DEMO']):
        assert turma.horarios_aula.exists(), turma.disciplina.codigo
    assert HorarioTurma.objects.count() == 3  # SEG + QUA (ES) e TER (BD), sem duplicar
    client.force_login(CustomUser.objects.get(email='coordenacao.demo@sga.edu.br'))
    grade = client.get(reverse('academics:grade_horaria')).content.decode()
    assert 'Engenharia de Software — Demo' in grade and 'Banco de Dados — Demo' in grade


# --- 3. Material só por download protegido -----------------------------------

@pytest.fixture
def material(turma, user_professor, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return MaterialAcademico.objects.create(
        turma=turma, autor=user_professor, titulo='Lista 1',
        arquivo=SimpleUploadedFile('Lista1.pdf', b'%PDF-conteudo', content_type='application/pdf'),
    )


@pytest.mark.django_db
def test_arquivo_salvo_em_pasta_aleatoria(material):
    partes = material.arquivo.name.split('/')
    assert partes[0] == 'materiais' and len(partes[1]) == 32 and partes[2] == 'Lista1.pdf'


@pytest.mark.django_db
def test_download_somente_para_quem_ve_a_turma(client, material, user_aluno, turma):
    url = reverse('materials:material_download', args=[material.pk])
    outro = CustomUser.objects.create_user(email='outro@sga.edu.br', full_name='Outro', role=UserRole.ALUNO,
                                           password='x', must_change_password=False)

    assert '/accounts/login' in client.get(url).url
    client.force_login(outro)
    assert client.get(url).status_code == 404

    Matricula.objects.create(aluno=user_aluno, turma=turma)
    client.force_login(user_aluno)
    resposta = client.get(url)
    assert resposta.status_code == 200
    assert b''.join(resposta.streaming_content) == b'%PDF-conteudo'
    assert 'Lista1.pdf' in resposta['Content-Disposition']


@pytest.mark.django_db
def test_media_nao_e_servida_diretamente(client, material, user_professor):
    client.force_login(user_professor)

    assert client.get('/media/' + material.arquivo.name).status_code == 404


@pytest.mark.django_db
def test_lista_de_materiais_aponta_para_download_protegido(client, material, user_professor):
    client.force_login(user_professor)

    html = client.get(reverse('materials:turma_materiais', args=[material.turma_id])).content.decode()

    assert reverse('materials:material_download', args=[material.pk]) in html
    assert material.arquivo.url not in html


# --- 4. Chamada não aceita data futura ---------------------------------------

@pytest.mark.django_db
def test_chamada_rejeita_data_futura_e_aceita_hoje(turma, user_professor, user_aluno):
    Matricula.objects.create(aluno=user_aluno, turma=turma)
    hoje = timezone.localdate()

    with pytest.raises(ValidationError, match='data futura'):
        registrar_chamada(user_professor, turma, hoje + timedelta(days=1), {user_aluno.pk: True})
    with pytest.raises(ValidationError, match='data futura'):
        registrar_chamada(user_professor, turma, (hoje + timedelta(days=7)).isoformat(), {user_aluno.pk: True})

    assert registrar_chamada(user_professor, turma, hoje, {user_aluno.pk: True})


@pytest.mark.django_db
def test_chamada_rejeita_data_invalida(turma, user_professor, user_aluno):
    Matricula.objects.create(aluno=user_aluno, turma=turma)

    with pytest.raises(ValidationError, match='data de aula válida'):
        registrar_chamada(user_professor, turma, '2026-02-31', {user_aluno.pk: True})


# --- 5. Turma com alunos não pode ser inativada ------------------------------

@pytest.mark.django_db
def test_inativar_turma_bloqueado_com_matricula_ativa(turma, user_aluno):
    matricula = Matricula.objects.create(aluno=user_aluno, turma=turma)

    with pytest.raises(ValidationError, match='1 matrícula'):
        inativar_turma(turma)
    turma.refresh_from_db()
    assert turma.ativo

    matricula.status = StatusMatricula.CONCLUIDA
    matricula.save(update_fields=['status'])
    assert not inativar_turma(turma).ativo


@pytest.mark.django_db
def test_tela_e_formulario_nao_inativam_turma_com_alunos(client, turma, user_aluno, user_coordenacao):
    Matricula.objects.create(aluno=user_aluno, turma=turma)
    client.force_login(user_coordenacao)

    resposta = client.post(reverse('academics:turma_inactivate', args=[turma.pk]), follow=True)
    assert 'matrícula(s) ativa(s)' in resposta.content.decode()
    turma.refresh_from_db()
    assert turma.ativo

    turma.ativo = False
    with pytest.raises(ValidationError) as erro:
        turma.full_clean()
    assert 'ativo' in erro.value.message_dict


# --- 6. Pré-requisito de disciplina inativa não bloqueia ---------------------

@pytest.mark.django_db
def test_pre_requisito_inativo_nao_bloqueia_matricula(turma, user_coordenacao, user_secretaria, user_aluno, user_professor):
    avancada = Disciplina.objects.create(nome='Algoritmos II', codigo='ALG2', carga_horaria=60,
                                         curso=turma.disciplina.curso)
    adicionar_pre_requisito(usuario=user_coordenacao, disciplina=avancada, requisito=turma.disciplina)
    turma_avancada = Turma.objects.create(disciplina=avancada, periodo_letivo='2027/1', horarios='TER 08:00-10:00',
                                          sala='B1', vagas_maximas=10, professor=user_professor)
    with pytest.raises(ValidationError, match='pré-requisitos'):
        matricular_aluno_administrativo(user_secretaria, user_aluno, turma_avancada)

    Disciplina.objects.filter(pk=turma.disciplina_id).update(ativo=False)

    assert matricular_aluno_administrativo(user_secretaria, user_aluno, turma_avancada)


# --- 7. CSV sem injeção de fórmula -------------------------------------------

@pytest.mark.django_db
def test_csv_neutraliza_formulas(client, turma, user_coordenacao):
    aluno = CustomUser.objects.create_user(email='formula@sga.edu.br', full_name='=HYPERLINK("http://x")',
                                           role=UserRole.ALUNO, password='x', must_change_password=False)
    Matricula.objects.create(aluno=aluno, turma=turma)
    client.force_login(user_coordenacao)

    conteudo = client.get(reverse('academics:relatorios_csv')).content.decode('utf-8-sig')

    assert '\'=HYPERLINK' in conteudo
    assert ',=HYPERLINK' not in conteudo


@pytest.mark.django_db
def test_tela_de_chamada_rejeita_data_futura_e_invalida_sem_erro_500(client, turma, user_professor, user_aluno):
    from attendance.models import Falta

    Matricula.objects.create(aluno=user_aluno, turma=turma)
    client.force_login(user_professor)
    url = reverse('attendance:chamada_lancar')
    amanha = (timezone.localdate() + timedelta(days=1)).isoformat()

    passo1 = client.post(url, {'step': '1', 'turma': turma.pk, 'data_aula': amanha})
    assert passo1.status_code == 200 and 'data futura' in passo1.content.decode()

    for data in (amanha, '2026-02-31'):
        passo2 = client.post(url, {'step': '2', 'turma_id': turma.pk, 'data_aula': data,
                                   f'presente_{user_aluno.pk}': 'on'}, follow=True)
        assert passo2.status_code == 200
    assert not Falta.objects.exists()
