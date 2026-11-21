import pytest
from django.core.exceptions import PermissionDenied
from academics.models import Curso, Disciplina, Turma
from accounts.models import UserRole
from communications.models import Comunicado, EscopoComunicado
from communications.services import publicar_comunicado, atualizar_comunicado, inativar_comunicado


@pytest.mark.django_db
class TestComunicadoServices:
    @pytest.fixture
    def setup_ambiente(self, user_secretaria, user_coordenacao, user_professor, user_aluno):
        curso = Curso.objects.create(codigo="ENG", nome="Engenharia")
        disciplina = Disciplina.objects.create(codigo="ENG101", nome="Cálculo", curso=curso, carga_horaria=60)
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026.1",
            horarios="SEX 08:00-10:00",
            vagas_maximas=40,
            professor=user_professor
        )
        return curso, turma, user_secretaria, user_coordenacao, user_professor, user_aluno

    def test_secretaria_publica_comunicado_geral_com_sucesso(self, setup_ambiente):
        _, _, sec, _, _, _ = setup_ambiente
        com = publicar_comunicado(
            autor=sec,
            titulo="Recesso de Carnaval",
            conteudo="Não haverá expediente.",
            escopo=EscopoComunicado.GERAL
        )
        assert com.pk is not None
        assert com.ativo is True

    def test_secretaria_publica_comunicado_por_papel(self, setup_ambiente):
        _, _, sec, _, _, _ = setup_ambiente
        com = publicar_comunicado(
            autor=sec,
            titulo="Aviso aos Alunos",
            conteudo="Renovação de carteirinha.",
            escopo=EscopoComunicado.PAPEL,
            papel_destino='ALUNO'
        )
        assert com.pk is not None
        assert com.papel_destino == 'ALUNO'

    def test_secretaria_bloqueada_para_comunicados_de_curso(self, setup_ambiente):
        curso, _, sec, _, _, _ = setup_ambiente
        with pytest.raises(PermissionDenied):
            publicar_comunicado(
                autor=sec,
                titulo="Aviso Engenharia",
                conteudo="Detalhes do curso",
                escopo=EscopoComunicado.CURSO,
                curso=curso
            )

    def test_secretaria_bloqueada_para_comunicados_de_turma(self, setup_ambiente):
        _, turma, sec, _, _, _ = setup_ambiente
        with pytest.raises(PermissionDenied):
            publicar_comunicado(
                autor=sec,
                titulo="Aviso da turma",
                conteudo="Detalhes da turma",
                escopo=EscopoComunicado.TURMA,
                turma=turma,
            )

    def test_coordenacao_publica_comunicado_de_curso_e_turma(self, setup_ambiente):
        curso, turma, _, coord, _, _ = setup_ambiente
        com_curso = publicar_comunicado(
            autor=coord,
            titulo="Mudança de Matriz",
            conteudo="Novas optativas",
            escopo=EscopoComunicado.CURSO,
            curso=curso
        )
        assert com_curso.pk is not None

        com_turma = publicar_comunicado(
            autor=coord,
            titulo="Troca de Sala",
            conteudo="Sala 104",
            escopo=EscopoComunicado.TURMA,
            turma=turma
        )
        assert com_turma.pk is not None

    def test_atualizar_comunicado(self, setup_ambiente):
        _, _, sec, _, _, _ = setup_ambiente
        com = publicar_comunicado(
            autor=sec,
            titulo="Aviso Inicial",
            conteudo="Texto inicial",
            escopo=EscopoComunicado.GERAL
        )
        atualizar_comunicado(
            comunicado=com,
            autor=sec,
            titulo="Aviso Corrigido",
            conteudo="Texto corrigido",
            escopo=EscopoComunicado.GERAL
        )
        com.refresh_from_db()
        assert com.titulo == "Aviso Corrigido"

    def test_professor_e_aluno_bloqueados_para_publicar(self, setup_ambiente):
        _, _, _, _, prof, aluno = setup_ambiente
        with pytest.raises(PermissionDenied):
            publicar_comunicado(
                autor=prof,
                titulo="Tentativa Professor",
                conteudo="Texto",
                escopo=EscopoComunicado.GERAL
            )
        with pytest.raises(PermissionDenied):
            publicar_comunicado(
                autor=aluno,
                titulo="Tentativa Aluno",
                conteudo="Texto",
                escopo=EscopoComunicado.GERAL
            )

    def test_inativar_comunicado(self, setup_ambiente):
        _, _, sec, _, _, _ = setup_ambiente
        com = publicar_comunicado(
            autor=sec,
            titulo="Aviso Temporário",
            conteudo="Será inativado logo",
            escopo=EscopoComunicado.GERAL
        )
        inativar_comunicado(comunicado=com, autor=sec)
        com.refresh_from_db()
        assert com.ativo is False
