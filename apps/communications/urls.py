from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('', views.mural_index, name='mural'),
    path('<int:pk>/', views.comunicado_detail, name='detail'),
    path('gestao/', views.comunicados_gestao, name='gestao'),
    path('novo/', views.comunicado_create, name='create'),
    path('<int:pk>/editar/', views.comunicado_update, name='update'),
    path('<int:pk>/inativar/', views.comunicado_inativar, name='inativar'),
]
