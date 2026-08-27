from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from accounts.decorators import role_required
from accounts.models import UserRole
from .selectors import get_matriculas_do_aluno
from .forms import MatriculaAdministrativaForm

@role_required(UserRole.SECRETARIA, UserRole.ALUNO)
def index_view(request):
    if request.user.role == UserRole.ALUNO:
        matriculas = get_matriculas_do_aluno(request.user)
        return render(request, 'enrollment/aluno_matriculas.html', {
            'title': 'Minhas Matrículas',
            'matriculas': matriculas,
        })
    return render(request, 'dashboards/secretaria.html', {'title': 'Gestão de Matrículas (Secretaria)'})


@role_required(UserRole.SECRETARIA)
def matricula_create_view(request):
    if request.method == 'POST':
        form = MatriculaAdministrativaForm(
            request.POST,
            usuario_secretaria=request.user,
        )
        if form.is_valid():
            try:
                form.save()
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, _("Matrícula realizada com sucesso."))
                return redirect('enrollment:matricula_create')
    else:
        form = MatriculaAdministrativaForm(usuario_secretaria=request.user)

    return render(
        request,
        'enrollment/matricula_form.html',
        {'form': form, 'title': 'Matrícula administrativa'},
    )
