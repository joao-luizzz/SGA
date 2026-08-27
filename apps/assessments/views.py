from django.shortcuts import render
from accounts.decorators import role_required
from accounts.models import UserRole

@role_required(UserRole.PROFESSOR, UserRole.ALUNO)
def index_view(request):
    title = 'Minhas Notas' if request.user.role == UserRole.ALUNO else 'Avaliações e Notas'
    return render(request, 'assessments/em_breve.html', {'title': title})
