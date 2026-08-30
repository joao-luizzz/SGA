"""
Testes de serviços de attendance e auditoria (Issues #12 e #13).
Cobre: registrar_chamada, integração com AuditoriaLog, imutabilidade do log.
"""
import pytest
from datetime import date
from django.core.exceptions import ValidationError

from accounts.models import AuditoriaLog, AcaoAuditoria, CustomUser, UserRole
from academics.models import Turma
from attendance.models import Falta
from attendance.services import registrar_chamada
from enrollment.models import Matricula, StatusMatricula


@pytest.mark.django_db
class TestRegistrarChamadaService:

    def test_rejeita_professor_de_outra_turma(
        self, turma, user_aluno, matricula_aluno
    ):
        outro_professor = CustomUser.objects.create_user(
            email='outro.professor@sga.edu.br',
            full_name='Outro Professor',
            role=UserRole.PROFESSOR,
            password='SenhaSegura123!',
        )

        with pytest.raises(ValidationError, match='professor responsável'):
            registrar_chamada(
                professor=outro_professor,
                turma=turma,
                data_aula=date(2026, 8, 18),
                presencas={user_aluno.pk: True},
            )

        assert Falta.objects.count() == 0
        assert AuditoriaLog.objects.count() == 0

    @pytest.mark.parametrize(
        'status',
        [None, StatusMatricula.CANCELADA, StatusMatricula.TRANCADA],
    )
    def test_rejeita_aluno_sem_matricula_ativa_na_turma(
        self, turma, user_professor, status
    ):
        aluno = CustomUser.objects.create_user(
            email=f'aluno.{status or "sem-matricula"}@sga.edu.br',
            full_name='Aluno sem matrícula ativa',
            role=UserRole.ALUNO,
            password='SenhaSegura123!',
        )
        if status:
            Matricula.objects.create(aluno=aluno, turma=turma, status=status)

        with pytest.raises(ValidationError, match='matrícula ativa'):
            registrar_chamada(
                professor=user_professor,
                turma=turma,
                data_aula=date(2026, 8, 18),
                presencas={aluno.pk: False},
            )

        assert Falta.objects.count() == 0
        assert AuditoriaLog.objects.count() == 0

    def test_rejeita_aluno_matriculado_apenas_em_outra_turma(
        self, turma, disciplina, user_professor
    ):
        aluno = CustomUser.objects.create_user(
            email='aluno.outra.turma@sga.edu.br',
            full_name='Aluno de outra turma',
            role=UserRole.ALUNO,
            password='SenhaSegura123!',
        )
        outra_turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/2',
            horarios='TER 08:00-10:00',
            sala='Lab 02',
            vagas_maximas=30,
            professor=user_professor,
            ativo=True,
        )
        Matricula.objects.create(
            aluno=aluno,
            turma=outra_turma,
            status=StatusMatricula.ATIVA,
        )

        with pytest.raises(ValidationError, match='matrícula ativa'):
            registrar_chamada(
                professor=user_professor,
                turma=turma,
                data_aula=date(2026, 8, 18),
                presencas={aluno.pk: True},
            )

        assert Falta.objects.count() == 0
        assert AuditoriaLog.objects.count() == 0

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

    def test_queryset_nao_pode_editar_nem_excluir(self, user_professor):
        log = self._criar_log(user_professor)
        with pytest.raises(ValueError, match='imutável'):
            AuditoriaLog.objects.filter(pk=log.pk).update(valor_novo='Alterado')
        with pytest.raises(ValueError, match='imutável'):
            AuditoriaLog.objects.filter(pk=log.pk).delete()

    def test_log_str_representation(self, user_professor):
        log = self._criar_log(user_professor)
        assert 'Falta' in str(log)
        assert 'CRIAR' in str(log)
