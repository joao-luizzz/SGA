import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from academics.models import HorarioTurma, Turma

def validar_horario_turma(horario_turma):
    """
    Valida as regras de negócio para um HorarioTurma específico:
    1. hora_inicio < hora_fim.
    2. Conflito de Professor: Professor alocado em outra turma no mesmo dia e horário sobrepostos no período letivo (RN09).
    3. Conflito de Turma: Turma alocada em duas disciplinas/aulas simultâneas no mesmo dia e horário sobrepostos no período letivo.
    4. Conflito de Sala: Sala alocada para outra turma no mesmo dia, horário sobrepostos e período letivo.
    """
    from django.core.exceptions import ObjectDoesNotExist
    try:
        turma = horario_turma.turma
    except ObjectDoesNotExist:
        return
    dia = horario_turma.dia_semana
    inicio = horario_turma.hora_inicio
    fim = horario_turma.hora_fim
    periodo = turma.periodo_letivo

    # 1. Inconsistência de intervalo
    if inicio and fim and inicio >= fim:
        raise ValidationError({
            'hora_inicio': _("A hora de início deve ser menor que a hora de término.")
        })

    # 2. Conflito de Professor
    if turma.professor:
        conflitos_prof = HorarioTurma.objects.filter(
            turma__ativo=True,
            turma__periodo_letivo=periodo,
            turma__professor=turma.professor,
            dia_semana=dia
        )
        if horario_turma.pk:
            conflitos_prof = conflitos_prof.exclude(pk=horario_turma.pk)
        
        for conf in conflitos_prof:
            if max(inicio, conf.hora_inicio) < min(fim, conf.hora_fim):
                raise ValidationError(
                    _("O professor %(professor)s já está alocado em outra turma ativa (%(turma)s) neste dia e horário conflitante (%(inicio)s-%(fim)s).") % {
                        'professor': turma.professor.full_name,
                        'turma': conf.turma.disciplina.nome,
                        'inicio': conf.hora_inicio.strftime('%H:%M'),
                        'fim': conf.hora_fim.strftime('%H:%M')
                    }
                )

    # 3. Conflito de Horário interno da Turma (Aulas sobrepostas da própria turma)
    conflitos_turma = HorarioTurma.objects.filter(
        turma__ativo=True,
        turma__periodo_letivo=periodo,
        turma=turma,
        dia_semana=dia
    )
    if horario_turma.pk:
        conflitos_turma = conflitos_turma.exclude(pk=horario_turma.pk)

    for conf in conflitos_turma:
        if max(inicio, conf.hora_inicio) < min(fim, conf.hora_fim):
            raise ValidationError(
                _("A turma já possui outra aula alocada neste dia e horário conflitante.")
            )

    # 4. Conflito de Sala (Sala em duas turmas simultâneas)
    if turma.sala:
        conflitos_sala = HorarioTurma.objects.filter(
            turma__ativo=True,
            turma__periodo_letivo=periodo,
            turma__sala=turma.sala,
            dia_semana=dia
        )
        if horario_turma.pk:
            conflitos_sala = conflitos_sala.exclude(pk=horario_turma.pk)

        conflitos_sala = conflitos_sala.exclude(turma=turma)

        for conf in conflitos_sala:
            if max(inicio, conf.hora_inicio) < min(fim, conf.hora_fim):
                raise ValidationError(
                    _("A sala %(sala)s já está sendo utilizada pela turma (%(turma)s) neste dia e horário conflitante.") % {
                        'sala': turma.sala,
                        'turma': conf.turma.disciplina.nome
                    }
                )


@transaction.atomic
def criar_horario_turma(turma, dia_semana, hora_inicio, hora_fim):
    """
    Cria e valida um HorarioTurma de forma atômica e segura.
    """
    horario = HorarioTurma(
        turma=turma,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim
    )
    horario.full_clean()
    horario.save()
    atualizar_campo_textual_turma(turma)
    return horario


def sincronizar_horarios_turma(turma):
    """
    Sincroniza os registros estruturados de HorarioTurma com o campo legado/textual Turma.horarios.
    A recriação é totalmente transacionada e valida todas as regras de negócio de HorarioTurma.
    """
    if turma.horarios:
        from academics.models import parse_horarios_lista
        from datetime import time

        try:
            parsed_list = parse_horarios_lista(turma.horarios)
        except ValidationError:
            # Se a string de horários legada estiver inválida ou malformada, não faz a sincronização
            return

        novos_horarios = []
        for dia, min_ini, min_fim in parsed_list:
            h_ini, m_ini = divmod(min_ini, 60)
            h_fim, m_fim = divmod(min_fim, 60)
            novos_horarios.append((dia, time(h_ini, m_ini), time(h_fim, m_fim)))

        existentes = list(turma.horarios_aula.all())
        existentes_tuples = [(h.dia_semana, h.hora_inicio, h.hora_fim) for h in existentes]

        if set(novos_horarios) != set(existentes_tuples):
            with transaction.atomic():
                turma.horarios_aula.all().delete()
                for dia, h_ini, h_fim in novos_horarios:
                    horario = HorarioTurma(
                        turma=turma,
                        dia_semana=dia,
                        hora_inicio=h_ini,
                        hora_fim=h_fim
                    )
                    horario.full_clean()
                    horario.save()
    else:
        # Se a string for esvaziada, remove os horários estruturados existentes de forma segura
        if turma.horarios_aula.exists():
            with transaction.atomic():
                turma.horarios_aula.all().delete()


def atualizar_campo_textual_turma(turma):
    """
    Atualiza o campo textual legado Turma.horarios a partir dos registros estruturados
    de HorarioTurma, garantindo consistência total e única fonte de verdade.
    """
    horarios_queryset = turma.horarios_aula.all().order_by('dia_semana', 'hora_inicio')
    partes = []
    for h in horarios_queryset:
        partes.append(f"{h.dia_semana} {h.hora_inicio.strftime('%H:%M')}-{h.hora_fim.strftime('%H:%M')}")

    novo_texto = ", ".join(partes)

    if turma.horarios != novo_texto:
        from academics.models import Turma
        Turma.objects.filter(pk=turma.pk).update(horarios=novo_texto)
        turma.horarios = novo_texto


def identificar_risco_academico(*, notas, resultado):
    """Sinaliza atenção com dados disponíveis, sem modificar o resultado oficial."""
    from decimal import Decimal
    from assessments.models import TipoAvaliacao
    from assessments.selectors import FREQUENCIA_MINIMA

    motivos = []
    frequencia = resultado['frequencia']
    if frequencia['total_aulas'] and frequencia['percentual'] < FREQUENCIA_MINIMA:
        motivos.append('Frequência registrada abaixo de 75%.')

    parciais = [notas[tipo] for tipo in (TipoAvaliacao.P1, TipoAvaliacao.P2, TipoAvaliacao.TRABALHO)
                if tipo in notas]
    # Usa as médias exatas, as mesmas que definem a situação oficial.
    media_final = resultado.get('media_final_exata', resultado['media_final'])
    media_parcial = resultado.get('media_parcial_exata', resultado['media_parcial'])
    if media_final is not None:
        if media_final < Decimal('6'):
            motivos.append('Média final abaixo de 6.')
    elif media_parcial is not None:
        if media_parcial < Decimal('6'):
            motivos.append('Média parcial abaixo de 6; confira a situação e o exame.')
    elif parciais and sum(parciais) / len(parciais) < Decimal('6'):
        motivos.append('Média das notas lançadas abaixo de 6 (avaliações incompletas).')

    incompletos = len(parciais) < 3 or not frequencia['total_aulas']
    return {
        'em_risco': bool(motivos),
        'rotulo': 'Em risco / atenção' if motivos else (
            'Dados insuficientes' if incompletos else 'Sem alerta nos dados disponíveis'),
        'motivos': motivos,
        'dados_incompletos': incompletos,
    }


# ---------------------------------------------------------------------------
# Pré-requisitos e aproveitamento de disciplinas (Fase 3 — RN18 a RN20, RN27)
# ---------------------------------------------------------------------------

CARGA_MINIMA_APROVEITAMENTO = Decimal('0.75')


def _exigir_papel(usuario, *papeis):
    from django.core.exceptions import PermissionDenied

    if not getattr(usuario, 'is_authenticated', False) or not usuario.is_active:
        raise PermissionDenied(_("Autentique-se para executar esta operação."))
    if not usuario.is_superuser and usuario.role not in papeis:
        raise PermissionDenied(_("Seu perfil não pode executar esta operação."))
    return usuario


def _estado_pre_requisito(pre_requisito):
    return json.dumps({
        'disciplina_id': pre_requisito.disciplina_id,
        'requisito_id': pre_requisito.requisito_id,
    }, sort_keys=True)


def _estado_aproveitamento(aproveitamento):
    return json.dumps({
        'aluno_id': aproveitamento.aluno_id,
        'disciplina_id': aproveitamento.disciplina_id,
        'instituicao_origem': aproveitamento.instituicao_origem,
        'disciplina_origem': aproveitamento.disciplina_origem,
        'carga_horaria_origem': aproveitamento.carga_horaria_origem,
        'status': aproveitamento.status,
        'analisado_por_id': aproveitamento.analisado_por_id,
        'justificativa': aproveitamento.justificativa,
    }, ensure_ascii=False, sort_keys=True)


def _gera_ciclo(disciplina_id, requisito_id):
    """True se `requisito` já depende (direta ou indiretamente) de `disciplina`."""
    from academics.models import PreRequisito

    visitados = set()
    fronteira = {requisito_id}
    while fronteira:
        if disciplina_id in fronteira:
            return True
        visitados |= fronteira
        fronteira = set(
            PreRequisito.objects.filter(disciplina_id__in=fronteira)
            .values_list('requisito_id', flat=True)
        ) - visitados
    return False


@transaction.atomic
def adicionar_pre_requisito(*, usuario, disciplina, requisito):
    from academics.models import Curso, Disciplina, PreRequisito
    from accounts.models import AcaoAuditoria, UserRole
    from accounts.services import registrar_auditoria

    _exigir_papel(usuario, UserRole.COORDENACAO)
    # Serializa alterações do grafo de um mesmo curso para que dois pedidos
    # concorrentes não criem um ciclo que nenhum deles enxergaria sozinho.
    Curso.objects.select_for_update().get(pk=disciplina.curso_id)
    disciplina = Disciplina.objects.get(pk=disciplina.pk)
    requisito = Disciplina.objects.get(pk=requisito.pk)

    if disciplina.pk == requisito.pk:
        raise ValidationError(_("Uma disciplina não pode ser pré-requisito de si mesma."))
    if disciplina.curso_id != requisito.curso_id:
        raise ValidationError(_("O pré-requisito deve pertencer ao mesmo curso da disciplina."))
    if not disciplina.ativo or not requisito.ativo:
        raise ValidationError(_("Somente disciplinas ativas podem receber ou ser pré-requisito."))
    if PreRequisito.objects.filter(disciplina=disciplina, requisito=requisito).exists():
        raise ValidationError(_("Este pré-requisito já está cadastrado."))
    if _gera_ciclo(disciplina.pk, requisito.pk):
        raise ValidationError(
            _("%(requisito)s já depende de %(disciplina)s; o cadastro criaria um ciclo.") % {
                'requisito': requisito.nome, 'disciplina': disciplina.nome,
            }
        )

    pre_requisito = PreRequisito.objects.create(disciplina=disciplina, requisito=requisito)
    registrar_auditoria(
        usuario=usuario, tabela_afetada='PreRequisito', registro_id=pre_requisito.pk,
        acao=AcaoAuditoria.CRIAR, valor_novo=_estado_pre_requisito(pre_requisito),
    )
    return pre_requisito


@transaction.atomic
def remover_pre_requisito(*, usuario, pre_requisito_id):
    from academics.models import PreRequisito
    from accounts.models import AcaoAuditoria, UserRole
    from accounts.services import registrar_auditoria

    _exigir_papel(usuario, UserRole.COORDENACAO)
    pre_requisito = PreRequisito.objects.select_for_update().get(pk=pre_requisito_id)
    anterior = _estado_pre_requisito(pre_requisito)
    registro_id = pre_requisito.pk
    pre_requisito.delete()
    registrar_auditoria(
        usuario=usuario, tabela_afetada='PreRequisito', registro_id=registro_id,
        acao=AcaoAuditoria.EXCLUIR, valor_antigo=anterior,
    )


@transaction.atomic
def registrar_aproveitamento(*, usuario, aluno, disciplina, instituicao_origem,
                             disciplina_origem, carga_horaria_origem):
    from academics.models import Aproveitamento, Disciplina, StatusAproveitamento
    from accounts.models import AcaoAuditoria, CustomUser, UserRole
    from accounts.services import registrar_auditoria

    _exigir_papel(usuario, UserRole.SECRETARIA)
    # Bloqueia o aluno para serializar registros equivalentes; a constraint
    # condicional continua como última barreira.
    aluno = CustomUser.objects.select_for_update().get(pk=aluno.pk)
    disciplina = Disciplina.objects.get(pk=disciplina.pk)
    if aluno.role != UserRole.ALUNO or not aluno.is_active:
        raise ValidationError({'aluno': _("Selecione um aluno ativo.")})
    if not disciplina.ativo:
        raise ValidationError({'disciplina': _("Selecione uma disciplina ativa.")})
    if Aproveitamento.objects.filter(
        aluno=aluno, disciplina=disciplina,
        status__in=[StatusAproveitamento.PENDENTE, StatusAproveitamento.DEFERIDO],
    ).exists():
        raise ValidationError(
            _("Já existe aproveitamento pendente ou deferido deste aluno para esta disciplina.")
        )

    aproveitamento = Aproveitamento(
        aluno=aluno, disciplina=disciplina,
        instituicao_origem=(instituicao_origem or '').strip(),
        disciplina_origem=(disciplina_origem or '').strip(),
        carga_horaria_origem=carga_horaria_origem,
        registrado_por=usuario,
    )
    aproveitamento.full_clean()
    try:
        with transaction.atomic():
            aproveitamento.save()
    except IntegrityError as exc:
        raise ValidationError(
            _("Já existe aproveitamento pendente ou deferido deste aluno para esta disciplina.")
        ) from exc
    registrar_auditoria(
        usuario=usuario, tabela_afetada='Aproveitamento', registro_id=aproveitamento.pk,
        acao=AcaoAuditoria.CRIAR, valor_novo=_estado_aproveitamento(aproveitamento),
    )
    return aproveitamento


@transaction.atomic
def analisar_aproveitamento(*, usuario, aproveitamento_id, decisao, justificativa):
    from django.utils import timezone

    from academics.models import Aproveitamento, StatusAproveitamento
    from accounts.models import AcaoAuditoria, UserRole
    from accounts.services import registrar_auditoria

    _exigir_papel(usuario, UserRole.COORDENACAO)
    if decisao not in (StatusAproveitamento.DEFERIDO, StatusAproveitamento.INDEFERIDO):
        raise ValidationError(_("Selecione deferimento ou indeferimento."))
    justificativa = (justificativa or '').strip()
    if not justificativa or len(justificativa) > 3000:
        raise ValidationError({'justificativa': _("Informe uma justificativa entre 1 e 3000 caracteres.")})

    aproveitamento = (
        Aproveitamento.objects.select_for_update().select_related('disciplina')
        .get(pk=aproveitamento_id)
    )
    if aproveitamento.status != StatusAproveitamento.PENDENTE:
        raise ValidationError(_("Este aproveitamento já foi analisado e não pode receber outra decisão."))
    carga_minima = aproveitamento.disciplina.carga_horaria * CARGA_MINIMA_APROVEITAMENTO
    if decisao == StatusAproveitamento.DEFERIDO and aproveitamento.carga_horaria_origem < carga_minima:
        raise ValidationError(
            _("Carga horária de origem insuficiente: o deferimento exige ao menos 75%% da carga "
              "da disciplina (%(minimo)s h).") % {'minimo': carga_minima.normalize()}
        )

    anterior = _estado_aproveitamento(aproveitamento)
    alterados = Aproveitamento.objects.filter(
        pk=aproveitamento.pk, status=StatusAproveitamento.PENDENTE,
    ).update(status=decisao, justificativa=justificativa,
             analisado_por=usuario, analisado_em=timezone.now())
    if alterados != 1:
        raise ValidationError(_("Este aproveitamento já foi analisado por outro usuário."))
    aproveitamento.refresh_from_db()
    registrar_auditoria(
        usuario=usuario, tabela_afetada='Aproveitamento', registro_id=aproveitamento.pk,
        acao=AcaoAuditoria.EDITAR, valor_antigo=anterior,
        valor_novo=_estado_aproveitamento(aproveitamento),
    )
    return aproveitamento


@transaction.atomic
def inativar_turma(turma):
    """Inativa a turma somente se não houver matrícula ativa (evita notas e frequência bloqueadas)."""
    from academics.models import Turma
    from enrollment.models import StatusMatricula

    turma = Turma.objects.select_for_update().get(pk=turma.pk)
    ativas = turma.matriculas.filter(status=StatusMatricula.ATIVA).count()
    if ativas:
        raise ValidationError(
            _("A turma possui %(n)d matrícula(s) ativa(s). Conclua, tranque ou cancele as "
              "matrículas antes de inativá-la.") % {'n': ativas}
        )
    turma.ativo = False
    turma.save(update_fields=['ativo'])
    return turma
