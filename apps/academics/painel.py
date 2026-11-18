"""Painel gerencial da Fase 3 (RN26): indicadores agregados, somente leitura."""
from django.shortcuts import render
from django.views.decorators.http import require_GET

from accounts.decorators import role_required
from accounts.models import UserRole

from .forms import FiltroRelatorioForm
from .selectors import get_indicadores_gerenciais


@role_required(UserRole.COORDENACAO, UserRole.SECRETARIA)
@require_GET
def painel_gerencial_view(request):
    filtros = FiltroRelatorioForm(request.GET)
    valido = filtros.is_valid()
    curso_id = filtros.cleaned_data['curso'] if valido else None
    periodo = filtros.cleaned_data['periodo'] if valido else ''
    contexto = get_indicadores_gerenciais(curso_id=curso_id, periodo=periodo)
    contexto.update({
        'title': 'Painel Gerencial',
        'filtro_curso': str(curso_id or ''),
        'filtro_periodo': periodo,
        'filtros_invalidos': not valido,
    })
    return render(request, 'academics/painel_gerencial.html', contexto, status=200 if valido else 400)
