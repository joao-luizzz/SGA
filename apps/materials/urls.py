from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.turma_materiais_index, name='index'),
    path('turma/<int:turma_id>/', views.turma_materiais_list, name='turma_materiais'),
    path('turma/<int:turma_id>/novo/', views.material_create, name='material_create'),
    path('<int:pk>/editar/', views.material_update, name='material_update'),
    path('<int:pk>/excluir/', views.material_delete, name='material_delete'),
]
