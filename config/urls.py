from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

handler403 = 'accounts.views.custom_permission_denied_view'
handler404 = 'accounts.views.custom_page_not_found_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='accounts:dashboard', permanent=False)),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('academics/', include('academics.urls', namespace='academics')),
    path('enrollment/', include('enrollment.urls', namespace='enrollment')),
    path('assessments/', include('assessments.urls', namespace='assessments')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
]
