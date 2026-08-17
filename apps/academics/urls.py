from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Catálogo Acadêmico (Listagem Unificada)
    path('', views.index_view, name='index'),
    
    # Cursos
    path('cursos/criar/', views.curso_create_view, name='curso_create'),
    path('cursos/<int:pk>/editar/', views.curso_update_view, name='curso_update'),
    path('cursos/<int:pk>/inativar/', views.curso_inactivate_view, name='curso_inactivate'),
    
    # Disciplinas
    path('disciplinas/criar/', views.disciplina_create_view, name='disciplina_create'),
    path('disciplinas/<int:pk>/editar/', views.disciplina_update_view, name='disciplina_update'),
    path('disciplinas/<int:pk>/inativar/', views.disciplina_inactivate_view, name='disciplina_inactivate'),
]
