from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from accounts.decorators import role_required
from accounts.models import UserRole
from .models import Matricula
from .selectors import get_matriculas_administrativas, get_matriculas_do_aluno
from .forms import MatriculaAdministrativaForm
from .services import alterar_status_matricula_administrativa

@role_required(UserRole.SECRETARIA, UserRole.ALUNO)
def index_view(request):
    if request.user.role == UserRole.ALUNO:
        matriculas = get_matriculas_do_aluno(request.user)
        return render(request, 'enrollment/aluno_matriculas.html', {
            'title': 'Minhas Matrículas',
            'matriculas': matriculas,
        })
    return render(request, 'enrollment/matricula_list.html', {
        'title': 'Gestão de Matrículas',
        'matriculas': get_matriculas_administrativas(),
    })


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
                return redirect('enrollment:index')
    else:
        form = MatriculaAdministrativaForm(usuario_secretaria=request.user)

    return render(
        request,
        'enrollment/matricula_form.html',
        {'form': form, 'title': 'Matrícula administrativa'},
    )


@role_required(UserRole.SECRETARIA)
@require_POST
def matricula_status_view(request, matricula_id):
    try:
        alterar_status_matricula_administrativa(
            usuario_secretaria=request.user,
            matricula_id=matricula_id,
            novo_status=request.POST.get('status'),
        )
    except Matricula.DoesNotExist:
        messages.error(request, _("Matrícula não encontrada."))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    else:
        messages.success(request, _("Status da matrícula atualizado com sucesso."))
    return redirect('enrollment:index')
