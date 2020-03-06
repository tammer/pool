from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='pool-home'),
    path('teams/', views.teams, name='pool-teams'),
    path('games/', views.games, name='pool-games'),
]