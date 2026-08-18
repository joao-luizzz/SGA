from django.db import models
from django.utils.translation import gettext_lazy as _

class Curso(models.Model):
    nome = models.CharField(_('nome'), max_length=150)
    codigo = models.CharField(_('código'), max_length=20, unique=True)
    descricao = models.TextField(_('descrição'), blank=True, null=True)
    ativo = models.BooleanField(_('ativo'), default=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('curso')
        verbose_name_plural = _('cursos')
        ordering = ['nome']

    def __str__(self):
        status = "" if self.ativo else f" ({_('Inativo')})"
        return f"{self.nome} - {self.codigo}{status}"


class Disciplina(models.Model):
    nome = models.CharField(_('nome'), max_length=100)
    codigo = models.CharField(_('código'), max_length=20, unique=True)
    carga_horaria = models.PositiveIntegerField(_('carga horária'))
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='disciplinas',
        verbose_name=_('curso')
    )
    ativo = models.BooleanField(_('ativo'), default=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('disciplina')
        verbose_name_plural = _('disciplinas')
        ordering = ['nome']

    def __str__(self):
        status = "" if self.ativo else f" ({_('Inativa')})"
        return f"{self.nome} - {self.codigo} ({self.carga_horaria}h){status}"


def parse_horarios_lista(horarios_str):
    """
    Interpreta uma string de horários que pode conter múltiplos horários separados por vírgula.
    Cada parte deve estar no formato "DIA HH:MM-HH:MM".
    Retorna uma lista de tuplas: [(dia_semana, minutos_inicio, minutos_fim), ...]
    Ex: "SEG 19:00-20:40, QUA 19:00-20:40" -> [("SEG", 1140, 1240), ("QUA", 1140, 1240)]
    """
    intervalos = []
    if not horarios_str:
        return intervalos
    partes = [p.strip() for p in horarios_str.replace(';', ',').split(',')]
    for parte in partes:
        if not parte:
            continue
        try:
            sub_parts = parte.strip().split()
            if len(sub_parts) < 2:
                continue
            dia = sub_parts[0].upper()
            intervalo = sub_parts[1]
            time_parts = intervalo.split('-')
            if len(time_parts) != 2:
                continue
            inicio_str, fim_str = time_parts[0].strip(), time_parts[1].strip()

            ih, im = map(int, inicio_str.split(':'))
            fh, fm = map(int, fim_str.split(':'))

            minutos_inicio = ih * 60 + im
            minutos_fim = fh * 60 + fm
            intervalos.append((dia, minutos_inicio, minutos_fim))
        except Exception:
            continue
    return intervalos



class Turma(models.Model):
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name='turmas',
        verbose_name=_('disciplina')
    )
    periodo_letivo = models.CharField(_('período letivo'), max_length=10)
    horarios = models.CharField(_('horários'), max_length=100)
    sala = models.CharField(_('sala'), max_length=30, blank=True, null=True)
    vagas_maximas = models.PositiveIntegerField(_('vagas máximas'))
    professor = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'PROFESSOR'},
        related_name='turmas_ministradas',
        verbose_name=_('professor')
    )
    ativo = models.BooleanField(_('ativo'), default=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('turma')
        verbose_name_plural = _('turmas')
        ordering = ['-periodo_letivo', 'disciplina__nome']

    def __str__(self):
        professor_str = self.professor.full_name if self.professor else _("Sem professor alocado")
        status = "" if self.ativo else f" ({_('Inativa')})"
        return f"{self.disciplina.nome} ({self.periodo_letivo}) - {professor_str}{status}"

    def clean(self):
        super().clean()
        # Impedir conflito de horário do professor (RN09)
        if self.ativo and self.professor and self.periodo_letivo and self.horarios:
            parsed_self_list = parse_horarios_lista(self.horarios)
            if parsed_self_list:
                conflitos = Turma.objects.filter(
                    ativo=True,
                    professor=self.professor,
                    periodo_letivo=self.periodo_letivo
                )
                if self.pk:
                    conflitos = conflitos.exclude(pk=self.pk)

                for conflito in conflitos:
                    parsed_conflito_list = parse_horarios_lista(conflito.horarios)
                    for dia_s, ini_s, fim_s in parsed_self_list:
                        for dia_c, ini_c, fim_c in parsed_conflito_list:
                            if dia_s == dia_c:
                                # Sobreposição real de intervalos de horários: max(ini_s, ini_c) < min(fim_s, fim_c)
                                if max(ini_s, ini_c) < min(fim_s, fim_c):
                                    from django.core.exceptions import ValidationError
                                    raise ValidationError({
                                        'horarios': _("O professor já está alocado em outra turma ativa neste período letivo com horário conflitante (%s: %s).") % (
                                            conflito.disciplina.nome, conflito.horarios
                                        )
                                    })


    def pode_receber_matricula(self):
        """
        Retorna True se a turma estiver ativa, com professor alocado,
        sala e horários configurados, e quantidade de vagas máximas maior que zero (RN40).
        """
        return (
            self.ativo and
            self.professor is not None and
            bool(self.horarios and self.horarios.strip()) and
            bool(self.sala and self.sala.strip()) and
            self.vagas_maximas is not None and self.vagas_maximas > 0
        )
