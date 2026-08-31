from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/aluno/', views.aluno_dashboard_view, name='dashboard_aluno'),
    path('dashboard/professor/', views.professor_dashboard_view, name='dashboard_professor'),
    path('dashboard/secretaria/', views.secretaria_dashboard_view, name='dashboard_secretaria'),
    path('dashboard/coordenacao/', views.coordenacao_dashboard_view, name='dashboard_coordenacao'),
    
    # Gerenciamento de Usuários (Secretaria)
    path('usuarios/', views.usuario_list_view, name='usuario_list'),
    path('usuarios/novo/', views.usuario_create_view, name='usuario_create'),
    path('usuarios/<int:user_id>/editar/', views.usuario_edit_view, name='usuario_edit'),
    path('usuarios/<int:user_id>/toggle-active/', views.usuario_toggle_active_view, name='usuario_toggle_active'),
]
