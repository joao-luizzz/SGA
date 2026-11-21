from django.urls import path
from . import views

app_name = 'notifications'
urlpatterns = [
    path('', views.central, name='central'),
    path('ler-todas/', views.ler_todas, name='ler_todas'),
    path('<int:pk>/', views.detalhe, name='detalhe'),
    path('<int:pk>/ler/', views.ler, name='ler'),
]
