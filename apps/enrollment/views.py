from django.shortcuts import render
from accounts.decorators import role_required
from accounts.models import UserRole
from .selectors import get_matriculas_do_aluno

@role_required(UserRole.SECRETARIA, UserRole.ALUNO)
def index_view(request):
    if request.user.role == UserRole.ALUNO:
        matriculas = get_matriculas_do_aluno(request.user)
        return render(request, 'enrollment/aluno_matriculas.html', {
            'title': 'Minhas Matrículas',
            'matriculas': matriculas,
        })
    return render(request, 'dashboards/secretaria.html', {'title': 'Gestão de Matrículas (Secretaria)'})
