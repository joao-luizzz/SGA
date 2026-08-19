"""
Testes de serviços de attendance e auditoria (Issues #12 e #13).
Cobre: registrar_chamada, integração com AuditoriaLog, imutabilidade do log.
"""
import pytest
from datetime import date

from accounts.models import AuditoriaLog, AcaoAuditoria
from attendance.models import Falta
from attendance.services import registrar_chamada


@pytest.mark.django_db
class TestRegistrarChamadaService:

    def test_cria_faltas_e_log_auditoria(self, turma, user_professor, user_aluno, matricula_aluno):
        """registrar_chamada cria Falta e AuditoriaLog para cada aluno (RN21, RN30)."""
        presencas = {user_aluno.pk: True}
        faltas = registrar_chamada(
            professor=user_professor,
            turma=turma,
            data_aula=date(2026, 8, 18),
            presencas=presencas,
        )
        assert len(faltas) == 1
        falta = faltas[0]
        assert falta.presente is True

        # Verifica auditoria (RN30)
        log = AuditoriaLog.objects.filter(
            tabela_afetada='Falta',
            registro_id=falta.pk,
            acao=AcaoAuditoria.CRIAR,
        ).first()
        assert log is not None
        assert log.usuario == user_professor
        assert log.valor_antigo is None
        assert 'Presente' in log.valor_novo

    def test_atualiza_chamada_e_gera_log_editar(self, turma, user_professor, user_aluno, matricula_aluno):
        """Ao relançar chamada da mesma data, gera log de EDITAR (RN30)."""
        data = date(2026, 8, 18)
        # Primeiro lançamento: presente
        registrar_chamada(
            professor=user_professor, turma=turma, data_aula=data,
            presencas={user_aluno.pk: True},
        )
        # Segundo lançamento: ausente
        registrar_chamada(
            professor=user_professor, turma=turma, data_aula=data,
            presencas={user_aluno.pk: False},
        )

        falta = Falta.objects.get(turma=turma, aluno=user_aluno, data_aula=data)
        assert falta.presente is False  # atualizado corretamente

        logs = AuditoriaLog.objects.filter(tabela_afetada='Falta', registro_id=falta.pk)
        assert logs.count() == 2  # CRIAR + EDITAR

        log_editar = logs.filter(acao=AcaoAuditoria.EDITAR).first()
        assert log_editar is not None
        assert 'Presente' in log_editar.valor_antigo
        assert 'Ausente' in log_editar.valor_novo


@pytest.mark.django_db
class TestAuditoriaLogImutabilidade:
    """Testa a imutabilidade do AuditoriaLog (RN31)."""

    def _criar_log(self, user_professor):
        return AuditoriaLog.objects.create(
            usuario=user_professor,
            tabela_afetada='Falta',
            registro_id=999,
            acao=AcaoAuditoria.CRIAR,
            valor_antigo=None,
            valor_novo='Presente',
        )

    def test_log_criado_com_sucesso(self, user_professor):
        log = self._criar_log(user_professor)
        assert log.pk is not None

    def test_log_nao_pode_ser_editado(self, user_professor):
        """Tentar salvar um log existente lança ValueError (RN31)."""
        log = self._criar_log(user_professor)
        log.valor_novo = 'Ausente'
        with pytest.raises(ValueError, match='imutável'):
            log.save()

    def test_log_nao_pode_ser_excluido(self, user_professor):
        """Tentar deletar um log lança ValueError (RN31)."""
        log = self._criar_log(user_professor)
        with pytest.raises(ValueError, match='imutável'):
            log.delete()

    def test_log_str_representation(self, user_professor):
        log = self._criar_log(user_professor)
        assert 'Falta' in str(log)
        assert 'CRIAR' in str(log)
