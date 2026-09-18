from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Catálogo Acadêmico (Listagem Unificada)
    path('', views.index_view, name='index'),
    path('relatorios/', views.relatorios_view, name='relatorios'),
    path('relatorios/exportar.csv', views.relatorios_csv_view, name='relatorios_csv'),
    
    # Cursos
    path('cursos/criar/', views.curso_create_view, name='curso_create'),
    path('cursos/<int:pk>/editar/', views.curso_update_view, name='curso_update'),
    path('cursos/<int:pk>/inativar/', views.curso_inactivate_view, name='curso_inactivate'),
    
    # Disciplinas
    path('disciplinas/criar/', views.disciplina_create_view, name='disciplina_create'),
    path('disciplinas/<int:pk>/editar/', views.disciplina_update_view, name='disciplina_update'),
    path('disciplinas/<int:pk>/inativar/', views.disciplina_inactivate_view, name='disciplina_inactivate'),

    # Turmas
    path('turmas/criar/', views.turma_create_view, name='turma_create'),
    path('turmas/<int:pk>/editar/', views.turma_update_view, name='turma_update'),
    path('turmas/<int:pk>/inativar/', views.turma_inactivate_view, name='turma_inactivate'),
    
    # Horários de Turma
    path('turmas/<int:turma_pk>/horarios/', views.turma_horarios_view, name='turma_horarios'),
    path('horarios/<int:pk>/deletar/', views.horario_delete_view, name='horario_delete'),
    
    # Grade Horária Semanal (Visão Geral por Perfil)
    path('grade-horaria/', views.grade_horaria_view, name='grade_horaria'),
]
