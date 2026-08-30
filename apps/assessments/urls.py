from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('turmas/<int:turma_id>/notas/', views.turma_notas_view, name='turma_notas'),
]
