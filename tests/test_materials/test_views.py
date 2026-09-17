import pytest
from django.urls import reverse
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole
from enrollment.models import Matricula, StatusMatricula
from materials.models import MaterialAcademico


@pytest.mark.django_db
class TestMaterialViews:
    @pytest.fixture
    def setup_cenario(self, client, user_professor, user_aluno, password):
        curso = Curso.objects.create(codigo="ADM", nome="Administração")
        disciplina = Disciplina.objects.create(codigo="ADM101", nome="Gestão", curso=curso, carga_horaria=60)
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026.1",
            horarios="QUI 19:00-22:00",
            vagas_maximas=40,
            professor=user_professor
        )
        Matricula.objects.create(aluno=user_aluno, turma=turma, status=StatusMatricula.ATIVA)
        material = MaterialAcademico.objects.create(
            turma=turma,
            autor=user_professor,
            titulo="Plano de Aula",
            link="https://adm.sga.edu.br"
        )
        return turma, material

    def test_usuario_anonimo_redirecionado_para_login(self, client):
        resp = client.get(reverse('materials:index'))
        assert resp.status_code == 302
        assert reverse('accounts:login') in resp.url

    def test_aluno_acessa_index_e_turmas_materiais(self, client, user_aluno, password, setup_cenario):
        turma, material = setup_cenario
        client.login(email=user_aluno.email, password=password)
        resp_idx = client.get(reverse('materials:index'))
        assert resp_idx.status_code == 200

        resp = client.get(reverse('materials:turma_materiais', kwargs={'turma_id': turma.id}))
        assert resp.status_code == 200
        assert "Plano de Aula" in resp.content.decode('utf-8')
        assert resp.context['pode_gerenciar'] is False

    def test_professor_publica_novo_material_via_post(self, client, user_professor, password, setup_cenario):
        turma, _ = setup_cenario
        client.login(email=user_professor.email, password=password)
        url_create = reverse('materials:material_create', kwargs={'turma_id': turma.id})

        # GET form
        resp_get = client.get(url_create)
        assert resp_get.status_code == 200

        # POST form
        resp = client.post(url_create, {
            'titulo': 'Exercício 1',
            'descricao': 'Resolver até sexta',
            'link': 'https://google.com'
        })
        assert resp.status_code == 302
        assert MaterialAcademico.objects.filter(titulo='Exercício 1').exists()

    def test_professor_edita_material_via_post(self, client, user_professor, password, setup_cenario):
        _, material = setup_cenario
        client.login(email=user_professor.email, password=password)
        url_edit = reverse('materials:material_update', kwargs={'pk': material.pk})

        resp_get = client.get(url_edit)
        assert resp_get.status_code == 200

        resp_post = client.post(url_edit, {
            'titulo': 'Plano de Aula Atualizado',
            'descricao': 'Nova versão',
            'link': 'https://adm.sga.edu.br/novo'
        })
        assert resp_post.status_code == 302
        material.refresh_from_db()
        assert material.titulo == 'Plano de Aula Atualizado'

    def test_professor_exclui_material_via_post(self, client, user_professor, password, setup_cenario):
        _, material = setup_cenario
        client.login(email=user_professor.email, password=password)
        url_del = reverse('materials:material_delete', kwargs={'pk': material.pk})

        resp_get = client.get(url_del)
        assert resp_get.status_code == 200

        resp_post = client.post(url_del)
        assert resp_post.status_code == 302
        assert not MaterialAcademico.objects.filter(pk=material.pk).exists()

    def test_aluno_bloqueado_para_criar_editar_e_excluir(self, client, user_aluno, password, setup_cenario):
        turma, material = setup_cenario
        client.login(email=user_aluno.email, password=password)

        resp_create = client.get(reverse('materials:material_create', kwargs={'turma_id': turma.id}))
        assert resp_create.status_code == 403

        resp_edit = client.get(reverse('materials:material_update', kwargs={'pk': material.pk}))
        assert resp_edit.status_code == 403

        resp_del = client.get(reverse('materials:material_delete', kwargs={'pk': material.pk}))
        assert resp_del.status_code == 403

    def test_aluno_nao_acessa_material_de_turma_sem_matricula(self, client, user_aluno, password, setup_cenario):
        turma, _ = setup_cenario
        outra_turma = Turma.objects.create(
            disciplina=turma.disciplina,
            periodo_letivo="2026.2",
            horarios="SEX 19:00-22:00",
            vagas_maximas=40,
            professor=turma.professor,
        )
        client.login(email=user_aluno.email, password=password)

        response = client.get(reverse('materials:turma_materiais', kwargs={'turma_id': outra_turma.id}))

        assert response.status_code == 403

    def test_professor_nao_edita_ou_exclui_material_de_outro_professor(self, client, user_professor, password, setup_cenario):
        turma, _ = setup_cenario
        outro_professor = CustomUser.objects.create_user(
            email="outro-professor@sga.edu.br",
            full_name="Outro Professor",
            role=UserRole.PROFESSOR,
            password=password,
            must_change_password=False,
        )
        outra_turma = Turma.objects.create(
            disciplina=turma.disciplina,
            periodo_letivo="2026.2",
            horarios="SEX 19:00-22:00",
            vagas_maximas=40,
            professor=outro_professor,
        )
        material = MaterialAcademico.objects.create(
            turma=outra_turma,
            autor=outro_professor,
            titulo="Material restrito",
            link="https://example.com/restrito",
        )
        client.login(email=user_professor.email, password=password)

        editar = client.get(reverse('materials:material_update', kwargs={'pk': material.pk}))
        excluir = client.get(reverse('materials:material_delete', kwargs={'pk': material.pk}))

        assert editar.status_code == 403
        assert excluir.status_code == 403

    def test_coordenacao_publica_e_secretaria_visualiza_materiais(self, client, user_coordenacao, user_secretaria, password, setup_cenario):
        turma, _ = setup_cenario
        client.login(email=user_coordenacao.email, password=password)

        publicar = client.post(reverse('materials:material_create', kwargs={'turma_id': turma.id}), {
            'titulo': 'Material da Coordenação',
            'descricao': '',
            'link': 'https://example.com/coordenacao',
        })

        assert publicar.status_code == 302
        client.login(email=user_secretaria.email, password=password)
        visualizar = client.get(reverse('materials:turma_materiais', kwargs={'turma_id': turma.id}))

        assert visualizar.status_code == 200
        assert 'Material da Coordenação' in visualizar.content.decode('utf-8')
