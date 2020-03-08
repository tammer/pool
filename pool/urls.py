from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='pool-home'),
    path('teams/', views.teams, name='pool-teams'),
    path('games/', views.games, name='pool-games'),
    path('results/', views.results, name='pool-results'),
    path('allpicks/', views.allpicks, name='pool-allpicks'),
    path('standings/', views.standings, name='pool-standings'),
]