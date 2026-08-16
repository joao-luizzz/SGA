from django.shortcuts import render
from accounts.decorators import role_required
from accounts.models import UserRole

@role_required(UserRole.PROFESSOR, UserRole.ALUNO)
def index_view(request):
    return render(request, 'dashboards/professor.html', {'title': 'Avaliações e Notas (Placeholder)'})
