import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from academics.models import Curso, Disciplina, Turma
from accounts.models import UserRole
from communications.models import Comunicado, EscopoComunicado


@pytest.mark.django_db
class TestComunicadoModel:
    @pytest.fixture
    def setup_curso_turma(self, user_professor):
        curso = Curso.objects.create(codigo="CC", nome="Ciência da Computação")
        disc = Disciplina.objects.create(codigo="CC101", nome="Algoritmos", curso=curso, carga_horaria=60)
        turma = Turma.objects.create(
            disciplina=disc,
            periodo_letivo="2026.1",
            horarios="QUA 08:00-10:00",
            vagas_maximas=30,
            professor=user_professor
        )
        return curso, turma

    def test_comunicado_geral_valido(self, user_secretaria):
        c = Comunicado(
            autor=user_secretaria,
            titulo="Início do Período Letivo",
            conteudo="Aulas iniciam dia 01/03.",
            escopo=EscopoComunicado.GERAL
        )
        c.full_clean()
        c.save()
        assert c.pk is not None
        assert c.is_vigente is True

    def test_comunicado_por_papel_exige_papel_destino(self, user_secretaria):
        c = Comunicado(
            autor=user_secretaria,
            titulo="Aviso Docente",
            conteudo="Reunião pedagógica",
            escopo=EscopoComunicado.PAPEL
        )
        with pytest.raises(ValidationError) as exc:
            c.full_clean()
        assert "papel_destino" in exc.value.message_dict

    def test_comunicado_por_curso_exige_curso(self, user_coordenacao):
        c = Comunicado(
            autor=user_coordenacao,
            titulo="Semana de TI",
            conteudo="Palestras",
            escopo=EscopoComunicado.CURSO
        )
        with pytest.raises(ValidationError) as exc:
            c.full_clean()
        assert "curso" in exc.value.message_dict

    def test_comunicado_por_turma_exige_turma(self, user_coordenacao):
        c = Comunicado(
            autor=user_coordenacao,
            titulo="Cancelamento de Aula",
            conteudo="Aula cancelada",
            escopo=EscopoComunicado.TURMA
        )
        with pytest.raises(ValidationError) as exc:
            c.full_clean()
        assert "turma" in exc.value.message_dict

    def test_data_expiracao_invalida_gera_erro(self, user_secretaria):
        agora = timezone.now()
        c = Comunicado(
            autor=user_secretaria,
            titulo="Teste Data",
            conteudo="Conteúdo",
            escopo=EscopoComunicado.GERAL,
            publicar_em=agora,
            expirar_em=agora - timedelta(days=1)
        )
        with pytest.raises(ValidationError) as exc:
            c.full_clean()
        assert "expirar_em" in exc.value.message_dict
