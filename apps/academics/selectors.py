from django.db.models import Count, Prefetch, Q

from assessments.models import Nota, TipoAvaliacao
from assessments.selectors import calcular_resultado_academico
from attendance.models import Falta
from enrollment.models import Matricula, StatusMatricula

from .models import Curso, Turma
from .services import identificar_risco_academico


def get_relatorio_turmas(*, curso_id=None, periodo=None, turma_id=None, risco=''):
    """Monta o relatório consolidado de turmas para a Coordenação."""
    matriculas_ativas = (
        Matricula.objects
        .filter(status=StatusMatricula.ATIVA)
        .select_related('aluno')
        .prefetch_related(Prefetch('notas', queryset=Nota.objects.order_by('tipo')))
        .order_by('aluno__full_name')
    )
    turmas = (
        Turma.objects
        .filter(ativo=True)
        .select_related('disciplina', 'disciplina__curso', 'professor')
        .prefetch_related(
            Prefetch(
                'matriculas',
                queryset=matriculas_ativas,
                to_attr='matriculas_relatorio',
            ),
            Prefetch(
                'faltas',
                queryset=Falta.objects.only('turma_id', 'aluno_id', 'presente'),
                to_attr='faltas_relatorio',
            ),
        )
        .annotate(
            matriculas_ativas=Count(
                'matriculas',
                filter=Q(matriculas__status=StatusMatricula.ATIVA),
            )
        )
        .order_by('-periodo_letivo', 'disciplina__nome')
    )

    if curso_id:
        turmas = turmas.filter(disciplina__curso_id=curso_id)
    if periodo:
        turmas = turmas.filter(periodo_letivo=periodo)
    if turma_id:
        turmas = turmas.filter(pk=turma_id)

    turmas = list(turmas)
    linhas = []
    for turma in turmas:
        turma.linhas_relatorio = []
        for matricula in turma.matriculas_relatorio:
            notas = {nota.tipo: nota.valor for nota in matricula.notas.all()}
            resultado = calcular_resultado_academico(matricula, notas)
            acompanhamento = identificar_risco_academico(notas=notas, resultado=resultado)
            if risco == 'sim' and not acompanhamento['em_risco']:
                continue
            if risco == 'nao' and acompanhamento['em_risco']:
                continue
            linha = {
                'turma': turma,
                'matricula': matricula,
                'aluno': matricula.aluno,
                'identificador_matricula': matricula.pk,
                'p1': notas.get(TipoAvaliacao.P1),
                'p2': notas.get(TipoAvaliacao.P2),
                'trabalho': notas.get(TipoAvaliacao.TRABALHO),
                'exame': notas.get(TipoAvaliacao.EXAME),
                'resultado': resultado,
                'risco': acompanhamento,
            }
            turma.linhas_relatorio.append(linha)
            linhas.append(linha)

    if risco:
        turmas = [turma for turma in turmas if turma.linhas_relatorio]
    return {
        'turmas': turmas,
        'linhas': linhas,
        'cursos': Curso.objects.filter(ativo=True).order_by('nome'),
        'periodos': (
            Turma.objects
            .filter(ativo=True)
            .values_list('periodo_letivo', flat=True)
            .distinct()
            .order_by('-periodo_letivo')
        ),
        'filtros': {
            'curso': str(curso_id or ''),
            'periodo': periodo or '',
            'turma': str(turma_id or ''),
            'risco': risco,
        },
    }


def listar_aproveitamentos(usuario, status=''):
    """Aluno vê somente os próprios; Secretaria, Coordenação e superusuário veem todos."""
    from accounts.models import UserRole
    from .models import Aproveitamento

    registros = Aproveitamento.objects.select_related(
        'aluno', 'disciplina__curso', 'registrado_por', 'analisado_por',
    )
    if not usuario.is_superuser and usuario.role == UserRole.ALUNO:
        registros = registros.filter(aluno=usuario)
    elif not usuario.is_superuser and usuario.role not in (UserRole.SECRETARIA, UserRole.COORDENACAO):
        return registros.none()
    if status:
        registros = registros.filter(status=status)
    return registros


def get_indicadores_gerenciais(*, curso_id=None, periodo=None):
    """Indicadores agregados do painel gerencial (RN26); somente leitura.

    Reutiliza o relatório consolidado para que situação acadêmica e risco
    sejam idênticos aos exibidos nos Relatórios Acadêmicos.
    """
    from collections import Counter

    from assessments.selectors import SituacaoAcademica
    from transfers.models import SolicitacaoTransferencia, StatusTransferencia

    from .models import Aproveitamento, StatusAproveitamento

    relatorio = get_relatorio_turmas(curso_id=curso_id, periodo=periodo)
    turmas = relatorio['turmas']
    linhas = relatorio['linhas']

    ocupacao = []
    matriculas_por_curso = Counter()
    for turma in turmas:
        vagas = turma.vagas_maximas or 0
        ocupacao.append({
            'turma': turma,
            'matriculados': turma.matriculas_ativas,
            'vagas': vagas,
            'percentual': round(turma.matriculas_ativas * 100 / vagas) if vagas else 0,
        })
        matriculas_por_curso[turma.disciplina.curso.nome] += turma.matriculas_ativas

    situacoes = Counter(linha['resultado']['situacao'] for linha in linhas)
    ordem = [
        SituacaoAcademica.APROVADO_DIRETO, SituacaoAcademica.APROVADO_EXAME,
        SituacaoAcademica.ELEGIVEL_EXAME, SituacaoAcademica.REPROVADO_NOTA,
        SituacaoAcademica.REPROVADO_FALTA, SituacaoAcademica.EM_ANDAMENTO,
    ]
    total = len(linhas)
    distribuicao = [
        {'situacao': s, 'quantidade': situacoes[s],
         'percentual': round(situacoes[s] * 100 / total) if total else 0}
        for s in ordem
    ]
    aprovados = situacoes[SituacaoAcademica.APROVADO_DIRETO] + situacoes[SituacaoAcademica.APROVADO_EXAME]
    reprovados = situacoes[SituacaoAcademica.REPROVADO_NOTA] + situacoes[SituacaoAcademica.REPROVADO_FALTA]
    concluidos = aprovados + reprovados

    transferencias = SolicitacaoTransferencia.objects.filter(status=StatusTransferencia.PENDENTE)
    aproveitamentos = Aproveitamento.objects.filter(status=StatusAproveitamento.PENDENTE)
    if curso_id:
        transferencias = transferencias.filter(curso_id=curso_id)
        aproveitamentos = aproveitamentos.filter(disciplina__curso_id=curso_id)

    vagas_totais = sum(item['vagas'] for item in ocupacao)
    matriculas_totais = sum(item['matriculados'] for item in ocupacao)
    return {
        'totais': {
            'turmas': len(turmas),
            'matriculas': matriculas_totais,
            'vagas': vagas_totais,
            'ocupacao': round(matriculas_totais * 100 / vagas_totais) if vagas_totais else 0,
            'em_risco': sum(1 for linha in linhas if linha['risco']['em_risco']),
            'taxa_aprovacao': round(aprovados * 100 / concluidos) if concluidos else None,
            'concluidos': concluidos,
        },
        'matriculas_por_curso': sorted(matriculas_por_curso.items()),
        'ocupacao': sorted(ocupacao, key=lambda item: -item['percentual']),
        'distribuicao': distribuicao,
        'pendencias': {
            'transferencias': transferencias.count(),
            'aproveitamentos': aproveitamentos.count(),
        },
        'cursos': relatorio['cursos'],
        'periodos': relatorio['periodos'],
    }
