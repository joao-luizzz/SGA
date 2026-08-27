from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Compatibilidade com sidebar existente
    path('', views.index_view, name='index'),

    # Professor — Chamada
    path('chamada/', views.chamada_index, name='chamada_index'),
    path('chamada/lancar/', views.chamada_lancar, name='chamada_lancar'),
    path('turma/<int:turma_id>/frequencia/', views.turma_frequencia_detail, name='turma_frequencia'),

    # Aluno — Boletim
    path('boletim/', views.boletim_frequencia, name='boletim_frequencia'),
]
