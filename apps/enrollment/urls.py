from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('administrativa/nova/', views.matricula_create_view, name='matricula_create'),
]
