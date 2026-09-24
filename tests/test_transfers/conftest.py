from datetime import date

import pytest

from academics.models import Curso
from transfers.services import solicitar_transferencia


@pytest.fixture
def curso_transferencia(db):
    return Curso.objects.create(nome='Sistemas de Informação', codigo='SI-TRANSF')


@pytest.fixture
def dados_transferencia(user_secretaria, user_aluno, curso_transferencia):
    return dict(usuario=user_secretaria, aluno=user_aluno, curso=curso_transferencia,
                tipo='SAIDA', instituicao_externa='Universidade Externa',
                curso_externo='Computação', data_referencia=date(2026, 9, 20),
                documentos='Histórico conferido pela secretaria; protocolo DOC-001.')


@pytest.fixture
def solicitacao(dados_transferencia):
    return solicitar_transferencia(**dados_transferencia)
