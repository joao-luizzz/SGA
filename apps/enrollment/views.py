from django.shortcuts import render
from accounts.decorators import role_required
from accounts.models import UserRole

@role_required(UserRole.SECRETARIA, UserRole.ALUNO)
def index_view(request):
    return render(request, 'dashboards/secretaria.html', {'title': 'Gestão de Matrículas (Placeholder)'})
