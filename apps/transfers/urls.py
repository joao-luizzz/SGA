from django.urls import path
from . import views

app_name = 'transfers'
urlpatterns = [
    path('', views.index, name='index'),
    path('criar/', views.criar, name='criar'),
    path('<int:pk>/', views.detalhe, name='detalhe'),
    path('<int:pk>/analisar/', views.analisar, name='analisar'),
]
