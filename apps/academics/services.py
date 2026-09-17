from django.core.exceptions import ValidationError
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
    turma = horario_turma.turma
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

    # 3. Conflito de Turma (Turma em duas disciplinas simultâneas)
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
                _("A turma já possui outra disciplina (%(disciplina)s) alocada neste dia e horário conflitante.") % {
                    'disciplina': conf.turma.disciplina.nome
                }
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
    return horario
