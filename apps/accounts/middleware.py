from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class MandatoryPasswordChangeMiddleware:
    """Middleware ensuring users with must_change_password=True change their password first."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, 'must_change_password', False):
            change_password_url = reverse('accounts:change_password')
            logout_url = reverse('accounts:logout')
            
            exempt_urls = [
                change_password_url,
                logout_url,
            ]
            
            path = request.path
            is_exempt = any(path.startswith(url) for url in exempt_urls) or path.startswith('/static/') or path.startswith('/admin/')

            if not is_exempt:
                messages.warning(
                    request,
                    _("Por motivos de segurança, você precisa alterar sua senha inicial antes de continuar.")
                )
                return redirect(change_password_url)

        return self.get_response(request)
