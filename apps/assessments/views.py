from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from accounts.decorators import role_required
from accounts.models import UserRole
from academics.models import Turma

from .forms import LancamentoNotasTurmaForm
from .models import TipoAvaliacao
from .selectors import (
    calcular_resultado_academico,
    get_boletim_do_aluno,
    get_matriculas_com_notas_da_turma,
    get_turmas_do_professor,
)
from .services import lancar_notas_em_lote


def _montar_linhas(form, matriculas):
    linhas = []
    for matricula in matriculas:
        linhas.append({
            'matricula': matricula,
            'p1': form[form.nome_campo(matricula.pk, TipoAvaliacao.P1)],
            'p2': form[form.nome_campo(matricula.pk, TipoAvaliacao.P2)],
            'trabalho': form[form.nome_campo(matricula.pk, TipoAvaliacao.TRABALHO)],
            'exame': form[form.nome_campo(matricula.pk, TipoAvaliacao.EXAME)],
            'resultado': calcular_resultado_academico(matricula),
        })
    return linhas

@role_required(UserRole.PROFESSOR, UserRole.ALUNO)
def index_view(request):
    if request.user.role == UserRole.ALUNO:
        return render(request, 'assessments/boletim.html', {
            'title': 'Meu Boletim',
            'boletim': get_boletim_do_aluno(request.user),
        })
    return render(request, 'assessments/turma_list.html', {
        'title': 'Avaliações e Notas',
        'turmas': get_turmas_do_professor(request.user),
    })


@role_required(UserRole.PROFESSOR)
def turma_notas_view(request, turma_id):
    turma = get_object_or_404(
        Turma.objects.select_related('disciplina'),
        pk=turma_id,
        professor=request.user,
        ativo=True,
    )
    matriculas = list(get_matriculas_com_notas_da_turma(turma))
    form = LancamentoNotasTurmaForm(
        request.POST or None,
        matriculas=matriculas,
    )
    if request.method == 'POST' and form.is_valid():
        try:
            lancar_notas_em_lote(
                professor=request.user,
                turma=turma,
                notas_por_matricula=form.get_notas_preenchidas(),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, _('Notas salvas com sucesso.'))
            return redirect('assessments:turma_notas', turma_id=turma.pk)

    return render(request, 'assessments/turma_notas.html', {
        'title': f'Notas — {turma.disciplina.nome}',
        'turma': turma,
        'form': form,
        'linhas': _montar_linhas(form, matriculas),
    })
