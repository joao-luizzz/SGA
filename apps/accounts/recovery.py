"""Views HTTP de recuperação de senha baseadas no fluxo nativo Django."""
from django.contrib.auth.views import (
    INTERNAL_RESET_SESSION_TOKEN, PasswordResetConfirmView, PasswordResetView,
)
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .forms import RecoveryForm, SGAMandatoryPasswordChangeForm
from .services import solicitar_recuperacao, redefinir_senha


class RecoveryHeadersMixin:
    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        response['Referrer-Policy'] = 'no-referrer'
        return response


class RecoveryRequestView(RecoveryHeadersMixin, PasswordResetView):
    form_class = RecoveryForm
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        solicitar_recuperacao(form, self.request)
        return HttpResponseRedirect(self.get_success_url())


class RecoveryConfirmView(RecoveryHeadersMixin, PasswordResetConfirmView):
    form_class = SGAMandatoryPasswordChangeForm
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        try:
            redefinir_senha(
                user_id=self.user.pk,
                token=self.request.session.get(INTERNAL_RESET_SESSION_TOKEN),
                password=form.cleaned_data['new_password1'],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        self.request.session.pop(INTERNAL_RESET_SESSION_TOKEN, None)
        return HttpResponseRedirect(self.get_success_url())
