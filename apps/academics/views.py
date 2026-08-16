from django.shortcuts import render
from accounts.decorators import role_required
from accounts.models import UserRole

@role_required(UserRole.COORDENACAO, UserRole.SECRETARIA)
def index_view(request):
    return render(request, 'dashboards/coordenacao.html', {'title': 'Gestão Acadêmica (Placeholder)'})
