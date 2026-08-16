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
]
