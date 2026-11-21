import pytest
from django.core.exceptions import PermissionDenied
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from enrollment.models import Matricula, StatusMatricula
from materials.models import MaterialAcademico
from materials.selectors import get_turmas_para_materiais, listar_materiais_turma, usuario_pode_acessar_turma


@pytest.mark.django_db
class TestMaterialSelectors:
    @pytest.fixture
    def setup_dados(self, user_professor, user_aluno, user_secretaria, user_coordenacao):
        curso = Curso.objects.create(codigo="MED", nome="Medicina")
        disciplina = Disciplina.objects.create(codigo="MED101", nome="Anatomia", curso=curso, carga_horaria=80)
        turma1 = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026.1",
            horarios="SEG 14:00-18:00",
            vagas_maximas=30,
            professor=user_professor
        )
        turma2 = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026.1",
            horarios="TER 14:00-18:00",
            vagas_maximas=30,
            professor=None
        )
        Matricula.objects.create(
            aluno=user_aluno,
            turma=turma1,
            status=StatusMatricula.ATIVA
        )
        mat1 = MaterialAcademico.objects.create(
            turma=turma1,
            autor=user_professor,
            titulo="Roteiro de Dissecação",
            link="https://med.edu.br/roteiro"
        )
        mat2 = MaterialAcademico.objects.create(
            turma=turma2,
            autor=user_professor,
            titulo="Material Turma 2",
            link="https://med.edu.br/t2"
        )
        return turma1, turma2, mat1, mat2, user_secretaria, user_coordenacao

    def test_aluno_matriculado_visualiza_apenas_suas_turmas_e_materiais(self, setup_dados, user_aluno):
        turma1, turma2, mat1, _, _, _ = setup_dados
        turmas = get_turmas_para_materiais(user_aluno)
        assert turma1 in turmas
        assert turma2 not in turmas

        materiais_t1 = listar_materiais_turma(turma1, user_aluno)
        assert mat1 in materiais_t1

        with pytest.raises(PermissionDenied):
            listar_materiais_turma(turma2, user_aluno)

    def test_professor_visualiza_turmas_ministradas(self, setup_dados, user_professor):
        turma1, turma2, mat1, _, _, _ = setup_dados
        turmas = get_turmas_para_materiais(user_professor)
        assert turma1 in turmas
        assert turma2 not in turmas

        materiais = listar_materiais_turma(turma1, user_professor)
        assert mat1 in materiais

    def test_secretaria_e_coordenacao_visualizam_todas_as_turmas(self, setup_dados):
        turma1, turma2, _, _, sec, coord = setup_dados
        turmas_sec = get_turmas_para_materiais(sec)
        assert turma1 in turmas_sec
        assert turma2 in turmas_sec

        turmas_coord = get_turmas_para_materiais(coord)
        assert turma1 in turmas_coord
        assert turma2 in turmas_coord

    def test_usuario_anonimo_retorna_vazio(self, setup_dados):
        turma1, _, _, _, _, _ = setup_dados
        assert not get_turmas_para_materiais(None).exists()
        assert usuario_pode_acessar_turma(turma1, None) is False
