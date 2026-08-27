"""
Testes de models e selectors da app attendance (Issue #12).
Cobre: Falta, cálculo de frequência, situações aprovado/reprovado por falta.
"""
import pytest
from datetime import date
from django.core.exceptions import ValidationError

from attendance.models import Falta
from attendance.selectors import (
    get_frequencia_do_aluno_na_turma,
    get_boletim_frequencia_do_aluno,
    get_datas_de_aula_da_turma,
    SituacaoFrequencia,
)


# -----------------------------------------------------------------------
# Testes de criação de Falta
# -----------------------------------------------------------------------

@pytest.mark.django_db
class TestFaltaModel:

    def test_cria_falta_presente(self, turma, user_aluno, user_professor, matricula_aluno, data_aula):
        falta = Falta.objects.create(
            turma=turma,
            aluno=user_aluno,
            data_aula=data_aula,
            presente=True,
            registrado_por=user_professor,
        )
        assert falta.pk is not None
        assert falta.presente is True
        assert 'Presente' in str(falta)

    def test_cria_falta_ausente(self, turma, user_aluno, user_professor, matricula_aluno, data_aula):
        falta = Falta.objects.create(
            turma=turma,
            aluno=user_aluno,
            data_aula=data_aula,
            presente=False,
            registrado_por=user_professor,
        )
        assert falta.presente is False
        assert 'Ausente' in str(falta)

    def test_unique_constraint_chamada(self, turma, user_aluno, user_professor, matricula_aluno, data_aula):
        """Não é permitido registrar duas faltas para o mesmo aluno/turma/data (RN21)."""
        from django.db import IntegrityError
        Falta.objects.create(
            turma=turma, aluno=user_aluno, data_aula=data_aula,
            presente=True, registrado_por=user_professor,
        )
        with pytest.raises(IntegrityError):
            Falta.objects.create(
                turma=turma, aluno=user_aluno, data_aula=data_aula,
                presente=False, registrado_por=user_professor,
            )

    def test_falta_requer_matricula_ativa(self, turma, user_aluno, user_professor):
        """Aluno sem matrícula ativa não pode ter falta registrada (clean)."""
        falta = Falta(
            turma=turma,
            aluno=user_aluno,
            data_aula=date(2026, 8, 15),
            presente=True,
            registrado_por=user_professor,
        )
        with pytest.raises(ValidationError):
            falta.full_clean()


# -----------------------------------------------------------------------
# Testes de cálculo de frequência
# -----------------------------------------------------------------------

@pytest.mark.django_db
class TestFrequenciaSelectors:

    def _criar_faltas(self, turma, aluno, professor, registros):
        """Helper: registros é lista de (data_str, presente)."""
        for data_str, presente in registros:
            Falta.objects.create(
                turma=turma,
                aluno=aluno,
                data_aula=date.fromisoformat(data_str),
                presente=presente,
                registrado_por=professor,
            )

    def test_frequencia_100_porcento(self, turma, user_aluno, user_professor, matricula_aluno):
        """Aluno com todas as presenças tem 100% de frequência."""
        self._criar_faltas(turma, user_aluno, user_professor, [
            ('2026-08-10', True),
            ('2026-08-17', True),
            ('2026-08-24', True),
            ('2026-08-31', True),
        ])
        freq = get_frequencia_do_aluno_na_turma(user_aluno, turma)
        assert freq['total_aulas'] == 4
        assert freq['presencas'] == 4
        assert freq['faltas'] == 0
        assert freq['percentual'] == 100
        assert freq['situacao'] == SituacaoFrequencia.APROVADO

    def test_frequencia_75_porcento_limite(self, turma, user_aluno, user_professor, matricula_aluno):
        """Aluno com exatamente 75% está aprovado (limite mínimo)."""
        self._criar_faltas(turma, user_aluno, user_professor, [
            ('2026-08-10', True),
            ('2026-08-17', True),
            ('2026-08-24', True),
            ('2026-08-31', False),
        ])
        freq = get_frequencia_do_aluno_na_turma(user_aluno, turma)
        assert freq['percentual'] == 75
        assert freq['situacao'] == SituacaoFrequencia.APROVADO

    def test_frequencia_abaixo_75_reprovado_falta(self, turma, user_aluno, user_professor, matricula_aluno):
        """Aluno com frequência < 75% é reprovado por falta (RN36)."""
        self._criar_faltas(turma, user_aluno, user_professor, [
            ('2026-08-10', True),
            ('2026-08-17', False),
            ('2026-08-24', False),
            ('2026-08-31', False),
        ])
        freq = get_frequencia_do_aluno_na_turma(user_aluno, turma)
        assert freq['percentual'] == 25
        assert freq['situacao'] == SituacaoFrequencia.REPROVADO_FALTA

    def test_frequencia_sem_aulas(self, turma, user_aluno, matricula_aluno):
        """Sem chamadas registradas, situação é 'Sem aulas registradas'."""
        freq = get_frequencia_do_aluno_na_turma(user_aluno, turma)
        assert freq['total_aulas'] == 0
        assert freq['situacao'] == SituacaoFrequencia.SEM_AULAS

    def test_get_datas_de_aula(self, turma, user_aluno, user_professor, matricula_aluno):
        """Retorna apenas datas distintas com chamada registrada."""
        self._criar_faltas(turma, user_aluno, user_professor, [
            ('2026-08-10', True),
            ('2026-08-17', False),
        ])
        datas = list(get_datas_de_aula_da_turma(turma))
        assert date(2026, 8, 10) in datas
        assert date(2026, 8, 17) in datas
        assert len(datas) == 2

    def test_boletim_frequencia_do_aluno(self, turma, user_aluno, user_professor, matricula_aluno):
        """Boletim retorna dados de frequência para todas as matrículas ativas."""
        Falta.objects.create(
            turma=turma, aluno=user_aluno, data_aula=date(2026, 8, 10),
            presente=True, registrado_por=user_professor,
        )
        boletim = get_boletim_frequencia_do_aluno(user_aluno)
        assert len(boletim) == 1
        assert boletim[0]['turma'] == turma
        assert boletim[0]['total_aulas'] == 1
