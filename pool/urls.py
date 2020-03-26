from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='pool-home'),
    path('teams/', views.teams, name='pool-teams'),
    path('games/', views.games, name='pool-games'),
    path('results/', views.results, name='pool-results'),
    path('allpicks/', views.allpicks, name='pool-allpicks'),
    path('standings/', views.standings, name='pool-standings'),
    path('overall/', views.overall, name='pool-overall'),
    path('money/', views.money, name='pool-money'),
    path('deposit/', views.deposit, name='pool-deposit'),
    path('blog/', views.blog, name='pool-blog'),
    path('post/', views.post, name='pool-post'),
    path('dopicks/', views.dopicks, name='pool-dopicks'),
    path('postpicks/', views.postpicks, name='pool-postpicks'),
]