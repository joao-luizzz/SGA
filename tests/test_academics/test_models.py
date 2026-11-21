import pytest
from academics.models import Curso, Disciplina, Turma
from accounts.models import CustomUser, UserRole

@pytest.mark.django_db
class TestAcademicsModels:
    def test_criar_curso(self):
        curso = Curso.objects.create(
            nome="Análise e Desenvolvimento de Sistemas",
            codigo="ADS",
            descricao="Curso de graduação tecnológica"
        )
        assert curso.nome == "Análise e Desenvolvimento de Sistemas"
        assert curso.codigo == "ADS"
        assert curso.ativo is True
        assert str(curso) == "Análise e Desenvolvimento de Sistemas - ADS"

    def test_criar_disciplina(self):
        curso = Curso.objects.create(
            nome="Análise e Desenvolvimento de Sistemas",
            codigo="ADS"
        )
        disciplina = Disciplina.objects.create(
            nome="Programação Orientada a Objetos",
            codigo="ADS-POO",
            carga_horaria=80,
            curso=curso
        )
        assert disciplina.nome == "Programação Orientada a Objetos"
        assert disciplina.codigo == "ADS-POO"
        assert disciplina.carga_horaria == 80
        assert disciplina.curso == curso
        assert disciplina.ativo is True
        assert str(disciplina) == "Programação Orientada a Objetos - ADS-POO (80h)"

    def test_inativacao_curso_nao_deleta_registro(self):
        curso = Curso.objects.create(
            nome="Sistemas de Informação",
            codigo="SI"
        )
        # Inativar curso
        curso.ativo = False
        curso.save()
        
        # Recarregar do banco de dados
        curso_db = Curso.objects.get(pk=curso.pk)
        assert curso_db is not None
        assert curso_db.ativo is False
        assert str(curso_db) == "Sistemas de Informação - SI (Inativo)"

    def test_inativacao_disciplina_nao_deleta_registro(self):
        curso = Curso.objects.create(
            nome="Sistemas de Informação",
            codigo="SI"
        )
        disciplina = Disciplina.objects.create(
            nome="Engenharia de Software",
            codigo="SI-ES",
            carga_horaria=60,
            curso=curso
        )
        # Inativar disciplina
        disciplina.ativo = False
        disciplina.save()
        
        # Recarregar do banco de dados
        disciplina_db = Disciplina.objects.get(pk=disciplina.pk)
        assert disciplina_db is not None
        assert disciplina_db.ativo is False
        assert str(disciplina_db) == "Engenharia de Software - SI-ES (60h) (Inativa)"


@pytest.mark.django_db
class TestTurmaModels:
    @pytest.fixture
    def setup_dados(self):
        curso = Curso.objects.create(nome="Análise e Desenvolvimento de Sistemas", codigo="ADS")
        disciplina = Disciplina.objects.create(nome="Programação Orientada a Objetos", codigo="ADS-POO", carga_horaria=80, curso=curso)
        professor = CustomUser.objects.create_user(
            email='professor_teste@sga.edu.br',
            full_name='Professor Teste',
            password='senha',
            role=UserRole.PROFESSOR
        )
        return {
            'curso': curso,
            'disciplina': disciplina,
            'professor': professor
        }

    def test_criar_turma_sem_professor(self, setup_dados):
        disciplina = setup_dados['disciplina']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40
        )
        assert turma.disciplina == disciplina
        assert turma.periodo_letivo == "2026/1"
        assert turma.horarios == "SEG 19:00-22:30"
        assert turma.vagas_maximas == 40
        assert turma.professor is None
        assert turma.ativo is True
        assert str(turma) == "Programação Orientada a Objetos (2026/1) - Sem professor alocado"

    def test_criar_turma_com_professor(self, setup_dados):
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40,
            professor=professor
        )
        assert turma.professor == professor
        assert str(turma) == "Programação Orientada a Objetos (2026/1) - Professor Teste"

    def test_metodo_pode_receber_matricula(self, setup_dados):
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']
        
        # 1. Sem professor (deve retornar False)
        turma_sem_prof = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            sala="Sala 101",
            vagas_maximas=40
        )
        assert turma_sem_prof.pode_receber_matricula() is False

        # 2. Com professor, sala, horário, vagas > 0 e ativa (deve retornar True)
        turma_com_tudo = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        assert turma_com_tudo.pode_receber_matricula() is True

        # 3. Com professor, mas inativa (deve retornar False)
        turma_com_tudo.ativo = False
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False
        turma_com_tudo.ativo = True
        turma_com_tudo.save()

        # 4. Sem sala (deve retornar False)
        turma_com_tudo.sala = ""
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False
        turma_com_tudo.sala = "Sala 101"
        turma_com_tudo.save()

        # 5. Sem horário (deve retornar False)
        turma_com_tudo.horarios = ""
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False
        turma_com_tudo.horarios = "SEG 19:00-22:30"
        turma_com_tudo.save()

        # 6. Vagas inválidas (<= 0) (deve retornar False)
        turma_com_tudo.vagas_maximas = 0
        turma_com_tudo.save()
        assert turma_com_tudo.pode_receber_matricula() is False

    def test_conflito_horario_professor(self, setup_dados):
        from django.core.exceptions import ValidationError
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']

        # Criar outro professor de teste
        outro_professor = CustomUser.objects.create_user(
            email='outro_prof@sga.edu.br',
            full_name='Outro Professor',
            password='senha',
            role=UserRole.PROFESSOR
        )

        # Turma base ativa para o Professor (SEG 19:00-20:40)
        turma_base = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-20:40",
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        # Executa clean() da turma_base (deve passar sem problemas)
        turma_base.clean()

        # 1. PERMITIR turmas com professores diferentes no mesmo horário/período
        turma_outro_prof = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-20:40",  # Horário idêntico
            sala="Sala 102",
            vagas_maximas=40,
            professor=outro_professor,
            ativo=True
        )
        turma_outro_prof.clean()  # Não deve levantar erro

        # 2. PERMITIR o mesmo professor em dias diferentes
        turma_outro_dia = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="TER 19:00-20:40",  # Horário igual, mas em dia diferente (TER)
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        turma_outro_dia.clean()  # Não deve levantar erro

        # 3. PERMITIR o mesmo professor em horários adjacentes (ex: Turma base termina 20:40, nova inicia 20:40)
        turma_adjacente = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 20:40-22:20",  # Adjacente
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        turma_adjacente.clean()  # Não deve levantar erro

        # 4. BLOQUEAR o mesmo professor em horários com sobreposição real parcial (ex: SEG 20:00-21:40 conflitante)
        turma_sobreposta_parcial = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 20:00-21:40",  # Conflita das 20:00 às 20:40
            sala="Sala 103",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        with pytest.raises(ValidationError) as excinfo:
            turma_sobreposta_parcial.clean()
        assert 'horarios' in excinfo.value.message_dict
        assert "horário conflitante" in excinfo.value.message_dict['horarios'][0]

        # 5. BLOQUEAR o mesmo professor em horários idênticos
        turma_identica = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-20:40",  # Horário idêntico
            sala="Sala 104",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        with pytest.raises(ValidationError) as excinfo:
            turma_identica.clean()
        assert 'horarios' in excinfo.value.message_dict
        assert "horário conflitante" in excinfo.value.message_dict['horarios'][0]

    def test_conflito_horario_multiplos_dias_com_barra(self, setup_dados):
        from django.core.exceptions import ValidationError
        disciplina = setup_dados['disciplina']
        professor = setup_dados['professor']

        # Turma base com múltiplos dias usando a barra / como separador (ex: SEG 19:00-20:40 / QUA 20:50-22:30)
        turma_multi = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-20:40 / QUA 20:50-22:30",
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        turma_multi.clean()  # Deve passar sem problemas

        # 1. PERMITIR segundo dia sem sobreposições
        turma_ok = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="QUA 19:00-20:40",  # Na quarta-feira, mas sem conflito com as 20:50-22:30
            sala="Sala 101",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        turma_ok.clean()  # Deve passar sem erros

        # 2. BLOQUEAR sobreposição no segundo dia (quarta-feira)
        turma_conflitante_quarta = Turma(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="QUA 21:00-22:00",  # Conflito real no segundo dia (quarta-feira) das 21h às 22h
            sala="Sala 102",
            vagas_maximas=40,
            professor=professor,
            ativo=True
        )
        with pytest.raises(ValidationError) as excinfo:
            turma_conflitante_quarta.clean()
        assert 'horarios' in excinfo.value.message_dict
        assert "horário conflitante" in excinfo.value.message_dict['horarios'][0]

    def test_validacao_horario_malformado(self, setup_dados):
        from django.core.exceptions import ValidationError
        disciplina = setup_dados['disciplina']

        horarios_invalidos = [
            "SEG 19:00",               # Falta horário de término
            "TER 19:00-abc",           # Termino não numérico
            "QQQ 19:00-20:00",         # Dia da semana inválido
            "SEG 25:00-26:00",         # Horas fora do limite de 24h
            "SEG 19:61-20:00",         # Minutos fora do limite de 60
            "SEG 20:00-19:00",         # Horário de início maior que término
            "SEG 19:00-20:40 / / QUA", # Separador redundante/vazio
        ]

        for horario_ruim in horarios_invalidos:
            turma_ruim = Turma(
                disciplina=disciplina,
                periodo_letivo="2026/1",
                horarios=horario_ruim,
                sala="Sala 101",
                vagas_maximas=40,
                ativo=True
            )
            with pytest.raises(ValidationError) as excinfo:
                turma_ruim.clean()
            assert 'horarios' in excinfo.value.message_dict

    def test_inativacao_turma_nao_deleta_registro(self, setup_dados):

        disciplina = setup_dados['disciplina']
        turma = Turma.objects.create(
            disciplina=disciplina,
            periodo_letivo="2026/1",
            horarios="SEG 19:00-22:30",
            vagas_maximas=40
        )
        turma.ativo = False
        turma.save()

        # Deve continuar no banco
        turma_db = Turma.objects.get(pk=turma.pk)
        assert turma_db is not None
        assert turma_db.ativo is False
        assert str(turma_db) == "Programação Orientada a Objetos (2026/1) - Sem professor alocado (Inativa)"


@pytest.mark.django_db
class TestHorarioTurmaConflitos:
    @pytest.fixture
    def setup_conflitos(self):
        curso = Curso.objects.create(nome="Analise de Sistemas", codigo="ADS")
        disc1 = Disciplina.objects.create(nome="POO", codigo="ADS-POO", carga_horaria=80, curso=curso)
        disc2 = Disciplina.objects.create(nome="Banco de Dados", codigo="ADS-BD", carga_horaria=80, curso=curso)
        
        prof1 = CustomUser.objects.create_user(
            email='prof1@sga.edu.br',
            full_name='Professor Um',
            password='senha',
            role=UserRole.PROFESSOR
        )
        prof2 = CustomUser.objects.create_user(
            email='prof2@sga.edu.br',
            full_name='Professor Dois',
            password='senha',
            role=UserRole.PROFESSOR
        )

        turma1 = Turma.objects.create(
            disciplina=disc1,
            periodo_letivo="2026/1",
            vagas_maximas=40,
            professor=prof1,
            sala="Sala 101",
            ativo=True
        )
        turma2 = Turma.objects.create(
            disciplina=disc2,
            periodo_letivo="2026/1",
            vagas_maximas=40,
            professor=prof2,
            sala="Sala 102",
            ativo=True
        )

        return {
            'turma1': turma1,
            'turma2': turma2,
            'prof1': prof1,
            'prof2': prof2,
        }

    def test_inconsistencia_intervalo(self, setup_conflitos):
        from django.core.exceptions import ValidationError
        from datetime import time
        from academics.models import HorarioTurma
        
        # hora_inicio == hora_fim
        h = HorarioTurma(
            turma=setup_conflitos['turma1'],
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(19, 0)
        )
        with pytest.raises(ValidationError) as excinfo:
            h.full_clean()
        assert 'hora_inicio' in excinfo.value.message_dict

        # hora_inicio > hora_fim
        h2 = HorarioTurma(
            turma=setup_conflitos['turma1'],
            dia_semana='SEG',
            hora_inicio=time(20, 0),
            hora_fim=time(19, 0)
        )
        with pytest.raises(ValidationError) as excinfo:
            h2.full_clean()
        assert 'hora_inicio' in excinfo.value.message_dict

    def test_conflito_professor_mesmo_horario(self, setup_conflitos):
        from django.core.exceptions import ValidationError
        from datetime import time
        from academics.models import HorarioTurma

        # Registrar horário para turma1 com prof1 (SEG 19:00 - 20:40)
        HorarioTurma.objects.create(
            turma=setup_conflitos['turma1'],
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )

        # Agora tentar registrar horário para turma2 com o prof1 também (sobreposição total)
        # Primeiro, vamos definir o prof1 na turma2
        turma2 = setup_conflitos['turma2']
        turma2.professor = setup_conflitos['prof1']
        turma2.save()

        h_conflito = HorarioTurma(
            turma=turma2,
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        with pytest.raises(ValidationError) as excinfo:
            h_conflito.full_clean()
        assert "__all__" in excinfo.value.message_dict
        assert "O professor" in excinfo.value.message_dict["__all__"][0]

    def test_conflito_professor_sobreposicao_parcial(self, setup_conflitos):
        from django.core.exceptions import ValidationError
        from datetime import time
        from academics.models import HorarioTurma

        HorarioTurma.objects.create(
            turma=setup_conflitos['turma1'],
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )

        # Definir mesmo professor na turma2
        turma2 = setup_conflitos['turma2']
        turma2.professor = setup_conflitos['prof1']
        turma2.save()

        # Horário: SEG 20:00 - 21:40 (conflita de 20:00 a 20:40)
        h_conflito = HorarioTurma(
            turma=turma2,
            dia_semana='SEG',
            hora_inicio=time(20, 0),
            hora_fim=time(21, 40)
        )
        with pytest.raises(ValidationError) as excinfo:
            h_conflito.full_clean()
        assert "__all__" in excinfo.value.message_dict
        assert "O professor" in excinfo.value.message_dict["__all__"][0]

    def test_conflito_turma_sobreposicao(self, setup_conflitos):
        from django.core.exceptions import ValidationError
        from datetime import time
        from academics.models import HorarioTurma

        # Remover professor para testar especificamente o conflito de turma
        turma1 = setup_conflitos['turma1']
        turma1.professor = None
        turma1.save()

        # Registrar horário para turma1 (SEG 19:00 - 20:40)
        h_setup = HorarioTurma(
            turma=turma1,
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        h_setup.full_clean()
        h_setup.save()

        # Registrar OUTRO horário para a MESMA turma1 (sobreposição)
        h_conflito = HorarioTurma(
            turma=turma1,
            dia_semana='SEG',
            hora_inicio=time(20, 0),
            hora_fim=time(21, 0)
        )
        with pytest.raises(ValidationError) as excinfo:
            h_conflito.full_clean()
        assert "__all__" in excinfo.value.message_dict
        assert "A turma já possui outra aula alocada" in excinfo.value.message_dict["__all__"][0]

    def test_conflito_sala_sobreposicao(self, setup_conflitos):
        from django.core.exceptions import ValidationError
        from datetime import time
        from academics.models import HorarioTurma

        # Colocar as duas turmas na mesma sala
        turma1 = setup_conflitos['turma1']
        turma2 = setup_conflitos['turma2']
        turma1.sala = "Sala 101"
        turma1.save()
        turma2.sala = "Sala 101"
        turma2.save()

        # Registrar para turma1 (SEG 19:00 - 20:40)
        h_setup = HorarioTurma(
            turma=turma1,
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        h_setup.full_clean()
        h_setup.save()

        # Registrar para turma2 na mesma sala (SEG 20:00 - 21:00)
        h_conflito = HorarioTurma(
            turma=turma2,
            dia_semana='SEG',
            hora_inicio=time(20, 0),
            hora_fim=time(21, 0)
        )
        with pytest.raises(ValidationError) as excinfo:
            h_conflito.full_clean()
        assert "__all__" in excinfo.value.message_dict
        assert "A sala Sala 101 já está sendo utilizada" in excinfo.value.message_dict["__all__"][0]

    def test_cadastro_sem_conflitos_sucesso(self, setup_conflitos):
        from datetime import time
        from academics.models import HorarioTurma

        # Registrar turma1: SEG 19:00 - 20:40
        h1 = HorarioTurma(
            turma=setup_conflitos['turma1'],
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        h1.full_clean() # Sucesso
        h1.save()

        # Registrar turma1: SEG 20:40 - 22:20 (adjacente, sem conflito)
        h2 = HorarioTurma(
            turma=setup_conflitos['turma1'],
            dia_semana='SEG',
            hora_inicio=time(20, 40),
            hora_fim=time(22, 20)
        )
        h2.full_clean() # Sucesso
        h2.save()

        # Registrar turma2: SEG 19:00 - 20:40 (salas e professores diferentes, sem conflito)
        h3 = HorarioTurma(
            turma=setup_conflitos['turma2'],
            dia_semana='SEG',
            hora_inicio=time(19, 0),
            hora_fim=time(20, 40)
        )
        h3.full_clean() # Sucesso
        h3.save()

