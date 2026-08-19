"""
Testes de views de attendance (Issue #12).
Cobre RBAC: professor lança chamada apenas em suas turmas; aluno consulta boletim.
"""
import pytest
from datetime import date
from django.urls import reverse

from attendance.models import Falta


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def login(client, user, password='SenhaSegura123!'):
    client.login(username=user.email, password=password)


# -----------------------------------------------------------------------
# Professor — Lançamento de chamada
# -----------------------------------------------------------------------

@pytest.mark.django_db
class TestChamadaIndexView:

    def test_professor_acessa_listagem_de_turmas(self, client, user_professor, turma, password):
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:chamada_index')
        response = client.get(url)
        assert response.status_code == 200
        assert turma.disciplina.nome.encode() in response.content

    def test_aluno_bloqueado_na_listagem(self, client, user_aluno, password):
        client.login(username=user_aluno.email, password=password)
        url = reverse('attendance:chamada_index')
        response = client.get(url)
        assert response.status_code == 403

    def test_secretaria_bloqueada_na_listagem(self, client, user_secretaria, password):
        client.login(username=user_secretaria.email, password=password)
        url = reverse('attendance:chamada_index')
        response = client.get(url)
        assert response.status_code == 403

    def test_anonimo_redirecionado(self, client):
        url = reverse('attendance:chamada_index')
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/' in response['Location']


@pytest.mark.django_db
class TestChamadaLancarView:

    def test_professor_acessa_formulario(self, client, user_professor, password):
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:chamada_lancar')
        response = client.get(url)
        assert response.status_code == 200

    def test_professor_submete_step1(self, client, user_professor, turma, matricula_aluno, password):
        """Passo 1: professor seleciona turma e data — deve exibir lista de alunos."""
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:chamada_lancar')
        response = client.post(url, {
            'step': '1',
            'turma': turma.pk,
            'data_aula': '2026-08-18',
        })
        assert response.status_code == 200
        # Deve mostrar o aluno matriculado
        assert user_professor.email.encode() not in response.content  # não é o professor
        # Formulário de chamada deve estar no contexto
        assert response.context['chamada_form'] is not None

    def test_professor_salva_chamada(self, client, user_professor, user_aluno, turma, matricula_aluno, password):
        """Passo 2: professor salva a chamada — falta deve ser criada."""
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:chamada_lancar')
        response = client.post(url, {
            'step': '2',
            'turma_id': turma.pk,
            'data_aula': '2026-08-18',
            f'presente_{user_aluno.pk}': 'on',  # checkbox marcado = presente
        })
        assert response.status_code == 302
        assert Falta.objects.filter(turma=turma, aluno=user_aluno, data_aula='2026-08-18').exists()

    def test_professor_nao_acessa_turma_alheia(self, client, user_professor, disciplina, password):
        """Professor sem vínculo com turma não consegue acessar a frequência dela."""
        from accounts.models import CustomUser, UserRole
        from academics.models import Turma
        outro_professor = CustomUser.objects.create_user(
            email='outro@sga.edu.br',
            full_name='Outro Professor',
            role=UserRole.PROFESSOR,
            password=password,
            must_change_password=False,
        )
        turma_alheia = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo='2026/1',
            horarios='TER 10:00-12:00',
            sala='Lab 02',
            vagas_maximas=20,
            professor=outro_professor,
            ativo=True,
        )
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:turma_frequencia', args=[turma_alheia.pk])
        response = client.get(url)
        assert response.status_code == 404  # get_object_or_404 filtra por professor=request.user


@pytest.mark.django_db
class TestTurmaFrequenciaView:

    def test_professor_ve_relatorio(self, client, user_professor, turma, password):
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:turma_frequencia', args=[turma.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_aluno_bloqueado_no_relatorio(self, client, user_aluno, turma, password):
        client.login(username=user_aluno.email, password=password)
        url = reverse('attendance:turma_frequencia', args=[turma.pk])
        response = client.get(url)
        assert response.status_code == 403


# -----------------------------------------------------------------------
# Aluno — Boletim de Frequência
# -----------------------------------------------------------------------

@pytest.mark.django_db
class TestBoletimFrequenciaView:

    def test_aluno_acessa_boletim(self, client, user_aluno, password):
        client.login(username=user_aluno.email, password=password)
        url = reverse('attendance:boletim_frequencia')
        response = client.get(url)
        assert response.status_code == 200

    def test_professor_bloqueado_no_boletim(self, client, user_professor, password):
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:boletim_frequencia')
        response = client.get(url)
        assert response.status_code == 403

    def test_boletim_exibe_turmas_matriculadas(self, client, user_aluno, turma, matricula_aluno, password):
        client.login(username=user_aluno.email, password=password)
        url = reverse('attendance:boletim_frequencia')
        response = client.get(url)
        assert response.status_code == 200
        assert turma.disciplina.nome.encode() in response.content

    def test_boletim_vazio_sem_matriculas(self, client, user_aluno, password):
        """Aluno sem matrículas vê boletim vazio (sem erro)."""
        client.login(username=user_aluno.email, password=password)
        url = reverse('attendance:boletim_frequencia')
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['boletim'] == []


@pytest.mark.django_db
class TestAttendanceIndexView:
    def test_index_redireciona_anonimo_para_login(self, client):
        url = reverse('attendance:index')
        response = client.get(url)
        assert response.status_code == 302
        assert reverse('accounts:login') in response.url

    def test_index_redireciona_professor_para_chamada(self, client, user_professor, password):
        client.login(username=user_professor.email, password=password)
        url = reverse('attendance:index')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse('attendance:chamada_index')

    def test_index_redireciona_aluno_para_boletim(self, client, user_aluno, password):
        client.login(username=user_aluno.email, password=password)
        url = reverse('attendance:index')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse('attendance:boletim_frequencia')

    def test_index_bloqueia_outros_perfis(self, client, user_coordenacao, password):
        client.login(username=user_coordenacao.email, password=password)
        url = reverse('attendance:index')
        response = client.get(url)
        assert response.status_code == 403

