from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from accounts.decorators import role_required
from accounts.models import UserRole
from academics.models import Turma
from enrollment.selectors import get_matriculas_ativas_da_turma

from .forms import SelecionarTurmaDataForm, ChamadaForm
from .models import Falta
from .selectors import (
    get_boletim_frequencia_do_aluno,
    get_datas_de_aula_da_turma,
    get_frequencia_do_aluno_na_turma,
    get_faltas_da_turma,
    get_chamada_por_turma_e_data,
)
from .services import registrar_chamada


# ---------------------------------------------------------------------------
# Views do Professor — Lançamento de Chamada
# ---------------------------------------------------------------------------

@role_required(UserRole.PROFESSOR)
def chamada_index(request):
    """Lista as turmas ativas do professor para que ele possa registrar chamada."""
    turmas = Turma.objects.filter(
        professor=request.user, ativo=True
    ).select_related('disciplina').order_by('-periodo_letivo', 'disciplina__nome')

    context = {
        'title': 'Registro de Frequência',
        'turmas': turmas,
    }
    return render(request, 'attendance/chamada_list.html', context)


@role_required(UserRole.PROFESSOR)
def chamada_lancar(request):
    """
    Permite ao professor selecionar turma + data e registrar a chamada.
    GET: exibe formulário de seleção de turma e data.
    POST (step 1): recebe turma e data, exibe lista de alunos para marcar presença.
    POST (step 2): salva a chamada.
    """
    form_selecao = SelecionarTurmaDataForm(professor=request.user)
    chamada_form = None
    turma_selecionada = None
    data_selecionada = None
    alunos_matriculados = []
    chamada_existente = []

    if request.method == 'POST':
        step = request.POST.get('step', '1')

        if step == '1':
            # Passo 1: professor selecionou turma e data — exibir lista de alunos
            form_selecao = SelecionarTurmaDataForm(request.POST, professor=request.user)
            if form_selecao.is_valid():
                turma_selecionada = form_selecao.cleaned_data['turma']
                data_selecionada = form_selecao.cleaned_data['data_aula']

                # Busca alunos matriculados ativamente nessa turma
                matriculas = get_matriculas_ativas_da_turma(turma_selecionada)
                alunos_matriculados = [m.aluno for m in matriculas]

                # Verifica se já existe chamada para essa data
                faltas_existentes = {
                    f.aluno_id: f.presente
                    for f in Falta.objects.filter(
                        turma=turma_selecionada, data_aula=data_selecionada
                    )
                }
                chamada_existente = bool(faltas_existentes)
                chamada_form = ChamadaForm(alunos=alunos_matriculados, faltas_existentes=faltas_existentes)

        elif step == '2':
            # Passo 2: professor confirmou a chamada — salvar
            from django.utils.dateparse import parse_date
            turma_id = request.POST.get('turma_id')
            data_aula_raw = request.POST.get('data_aula')
            data_aula = parse_date(data_aula_raw) if data_aula_raw else None
            turma_selecionada = get_object_or_404(Turma, pk=turma_id, professor=request.user)

            matriculas = get_matriculas_ativas_da_turma(turma_selecionada)
            alunos_matriculados = [m.aluno for m in matriculas]

            chamada_form = ChamadaForm(request.POST, alunos=alunos_matriculados)
            if chamada_form.is_valid() and data_aula:
                presencas = chamada_form.get_presencas()
                registrar_chamada(
                    professor=request.user,
                    turma=turma_selecionada,
                    data_aula=data_aula,
                    presencas=presencas,
                )
                messages.success(
                    request,
                    _("Chamada registrada com sucesso para %(turma)s em %(data)s.") % {
                        'turma': turma_selecionada.disciplina.nome,
                        'data': data_aula.strftime('%d/%m/%Y'),
                    }
                )
                return redirect('attendance:chamada_index')
            else:
                data_selecionada = data_aula
                messages.error(request, _("Erro ao salvar a chamada. Verifique os dados e tente novamente."))

    context = {
        'title': 'Registrar Chamada',
        'form_selecao': form_selecao,
        'chamada_form': chamada_form,
        'turma_selecionada': turma_selecionada,
        'data_selecionada': data_selecionada,
        'alunos_matriculados': alunos_matriculados,
        'chamada_existente': chamada_existente if isinstance(chamada_existente, bool) else False,
    }
    return render(request, 'attendance/chamada_form.html', context)


@role_required(UserRole.PROFESSOR)
def turma_frequencia_detail(request, turma_id):
    """
    Exibe o relatório de frequência consolidado de uma turma (por professor).
    Somente o professor responsável pode acessar (RN02).
    """
    turma = get_object_or_404(Turma, pk=turma_id, professor=request.user, ativo=True)
    matriculas = get_matriculas_ativas_da_turma(turma)
    alunos = [m.aluno for m in matriculas]

    datas_de_aula = list(get_datas_de_aula_da_turma(turma))
    total_aulas = len(datas_de_aula)

    # Monta tabela: cada aluno com sua frequência
    relatorio = []
    for aluno in alunos:
        freq = get_frequencia_do_aluno_na_turma(aluno, turma)
        relatorio.append({
            'aluno': aluno,
            **freq,
        })

    context = {
        'title': f'Frequência — {turma.disciplina.nome}',
        'turma': turma,
        'datas_de_aula': datas_de_aula,
        'total_aulas': total_aulas,
        'relatorio': relatorio,
    }
    return render(request, 'attendance/turma_frequencia.html', context)


# ---------------------------------------------------------------------------
# Views do Aluno — Boletim de Frequência
# ---------------------------------------------------------------------------

@role_required(UserRole.ALUNO)
def boletim_frequencia(request):
    """
    Exibe o boletim de frequência do aluno logado em todas as turmas onde está matriculado.
    (RN03, RN22, RN23, RN36)
    """
    boletim = get_boletim_frequencia_do_aluno(request.user)

    context = {
        'title': 'Meu Boletim de Frequência',
        'boletim': boletim,
    }
    return render(request, 'attendance/boletim_aluno.html', context)


# ---------------------------------------------------------------------------
# View de índice legada (placeholder compatível)
# ---------------------------------------------------------------------------

def index_view(request):
    """Redireciona para a view adequada conforme o perfil do usuário."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if request.user.role == UserRole.PROFESSOR:
        return redirect('attendance:chamada_index')
    if request.user.role == UserRole.ALUNO:
        return redirect('attendance:boletim_frequencia')
    from django.core.exceptions import PermissionDenied
    raise PermissionDenied
