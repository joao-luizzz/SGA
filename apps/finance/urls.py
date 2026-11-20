from django.urls import path

from . import views

app_name = 'finance'
urlpatterns = [
    path('', views.index, name='index'),
    path('nova/', views.criar, name='criar'),
    path('<int:pk>/', views.detalhe, name='detalhe'),
    path('<int:pk>/pagar/', views.pagar, name='pagar'),
    path('<int:pk>/cancelar/', views.cancelar, name='cancelar'),
]
