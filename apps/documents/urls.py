from django.urls import path

from . import views

app_name = 'documents'
urlpatterns = [
    path('', views.index, name='index'),
    path('emitir/', views.emitir, name='emitir'),
    path('<int:pk>/', views.detalhe, name='detalhe'),
    path('verificar/', views.verificar, name='verificar'),
]
