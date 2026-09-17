from django.core.exceptions import ValidationError
from django.db import transaction
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
