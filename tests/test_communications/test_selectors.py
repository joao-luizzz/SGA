import pytest
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from communications.models import Comunicado, EscopoComunicado
from communications.selectors import listar_comunicados_para_usuario, listar_comunicados_gerenciamento
from enrollment.models import Matricula, StatusMatricula


@pytest.mark.django_db
class TestComunicadoSelectors:
    @pytest.fixture
    def setup_dados(self, user_secretaria, user_aluno, user_professor, user_coordenacao):
        curso1 = Curso.objects.create(codigo="CC", nome="Computação")
        curso2 = Curso.objects.create(codigo="DIR", nome="Direito")

        d1 = Disciplina.objects.create(codigo="CC101", nome="Prog 1", curso=curso1, carga_horaria=60)
        d2 = Disciplina.objects.create(codigo="DIR101", nome="Dir 1", curso=curso2, carga_horaria=60)

        t1 = Turma.objects.create(disciplina=d1, periodo_letivo="2026.1", horarios="SEG 08:00-10:00", vagas_maximas=30, professor=user_professor)
        t2 = Turma.objects.create(disciplina=d2, periodo_letivo="2026.1", horarios="TER 08:00-10:00", vagas_maximas=30, professor=None)

        Matricula.objects.create(aluno=user_aluno, turma=t1, status=StatusMatricula.ATIVA)

        # Comunicados de diferentes escopos
        c_geral = Comunicado.objects.create(autor=user_secretaria, titulo="Geral", conteudo="...", escopo=EscopoComunicado.GERAL)
        c_aluno = Comunicado.objects.create(autor=user_secretaria, titulo="Só Aluno", conteudo="...", escopo=EscopoComunicado.PAPEL, papel_destino='ALUNO')
        c_prof = Comunicado.objects.create(autor=user_secretaria, titulo="Só Professor", conteudo="...", escopo=EscopoComunicado.PAPEL, papel_destino='PROFESSOR')
        c_curso_cc = Comunicado.objects.create(autor=user_secretaria, titulo="Curso CC", conteudo="...", escopo=EscopoComunicado.CURSO, curso=curso1)
        c_curso_dir = Comunicado.objects.create(autor=user_secretaria, titulo="Curso DIR", conteudo="...", escopo=EscopoComunicado.CURSO, curso=curso2)
        c_turma_t1 = Comunicado.objects.create(autor=user_secretaria, titulo="Turma T1", conteudo="...", escopo=EscopoComunicado.TURMA, turma=t1)
        c_turma_t2 = Comunicado.objects.create(autor=user_secretaria, titulo="Turma T2", conteudo="...", escopo=EscopoComunicado.TURMA, turma=t2)

        return c_geral, c_aluno, c_prof, c_curso_cc, c_curso_dir, c_turma_t1, c_turma_t2, user_coordenacao

    def test_aluno_visualiza_apenas_comunicados_pertinentes(self, setup_dados, user_aluno):
        c_geral, c_aluno, c_prof, c_curso_cc, c_curso_dir, c_turma_t1, c_turma_t2, _ = setup_dados
        visiveis = listar_comunicados_para_usuario(user_aluno)

        assert c_geral in visiveis
        assert c_aluno in visiveis
        assert c_curso_cc in visiveis
        assert c_turma_t1 in visiveis

        assert c_prof not in visiveis
        assert c_curso_dir not in visiveis
        assert c_turma_t2 not in visiveis

    def test_professor_visualiza_apenas_comunicados_pertinentes(self, setup_dados, user_professor):
        c_geral, c_aluno, c_prof, c_curso_cc, c_curso_dir, c_turma_t1, c_turma_t2, _ = setup_dados
        visiveis = listar_comunicados_para_usuario(user_professor)

        assert c_geral in visiveis
        assert c_prof in visiveis
        assert c_curso_cc in visiveis
        assert c_turma_t1 in visiveis

        assert c_aluno not in visiveis
        assert c_curso_dir not in visiveis
        assert c_turma_t2 not in visiveis

    def test_coordenacao_e_secretaria_visualizam_todos_no_mural_e_gestao(self, setup_dados, user_secretaria):
        c_geral, c_aluno, c_prof, c_curso_cc, c_curso_dir, c_turma_t1, c_turma_t2, coord = setup_dados

        mural_coord = listar_comunicados_para_usuario(coord)
        assert mural_coord.count() == 7

        gestao_sec = listar_comunicados_gerenciamento(user_secretaria)
        assert gestao_sec.count() == 7

    def test_usuario_anonimo_retorna_vazio(self):
        assert not listar_comunicados_para_usuario(None).exists()
        assert not listar_comunicados_gerenciamento(None).exists()
