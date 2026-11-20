"""Correções da conferência visual no navegador (#63)."""
from datetime import time
from decimal import Decimal

import pytest
from django.urls import reverse

from academics.models import Curso, Disciplina, HorarioTurma, Turma
from assessments.models import Nota, TipoAvaliacao
from documents.models import TipoDocumento
from documents.services import emitir_documento
from enrollment.models import Matricula


@pytest.fixture
def turma(db, user_professor):
    curso = Curso.objects.create(nome='Sistemas', codigo='SI')
    disciplina = Disciplina.objects.create(nome='Algoritmos', codigo='ALG', carga_horaria=60, curso=curso)
    turma = Turma.objects.create(disciplina=disciplina, periodo_letivo='2026/2', horarios='SEG 08:00-10:00',
                                 sala='Laboratório 07', vagas_maximas=10, professor=user_professor)
    HorarioTurma.objects.create(turma=turma, dia_semana='SEG', hora_inicio=time(8), hora_fim=time(10))
    return turma


@pytest.mark.django_db
def test_sidebar_recolhivel_no_celular_com_botao_menu(client, user_aluno):
    client.force_login(user_aluno)

    html = client.get(reverse('accounts:dashboard_aluno')).content.decode()

    assert 'id="sidebarMenu"' in html and 'collapse d-md-block' in html
    assert 'data-bs-target="#sidebarMenu"' in html


@pytest.mark.django_db
def test_menu_mobile_nao_aparece_para_anonimo(client):
    assert 'data-bs-target="#sidebarMenu"' not in client.get(reverse('accounts:login')).content.decode()


@pytest.mark.django_db
def test_grade_do_professor_mostra_a_sala(client, user_professor, turma):
    client.force_login(user_professor)

    html = client.get(reverse('academics:grade_horaria')).content.decode()

    assert 'Sala: Laboratório 07' in html


@pytest.mark.django_db
def test_historico_usa_virgula_decimal_e_tabela_rolavel(client, user_aluno, user_professor, turma):
    matricula = Matricula.objects.create(aluno=user_aluno, turma=turma)
    for tipo in (TipoAvaliacao.P1, TipoAvaliacao.P2, TipoAvaliacao.TRABALHO):
        Nota.objects.create(matricula=matricula, tipo=tipo, valor=Decimal('8'), registrado_por=user_professor)
    documento = emitir_documento(usuario=user_aluno, aluno=user_aluno, tipo=TipoDocumento.HISTORICO)
    client.force_login(user_aluno)

    html = client.get(reverse('documents:detalhe', args=[documento.pk])).content.decode()

    assert '8,00' in html and '100,0%' in html
    assert 'table-responsive' in html
