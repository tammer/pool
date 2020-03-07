from django.core.management.base import BaseCommand, CommandError
from pool.models import Team,Game
from random import choice

class Command(BaseCommand):
	help = 'Load some spreads and scores into existing games (for testing)'

	def handle(self, *args, **options):

		for game in Game.objects.all():
			game.fav_score = choice([10,14,20,21,35,40])
			game.udog_score = choice([7,10,14,20,21,35])
			game.spread = choice([3.5,7.5,10.5])
			game.fav_is_home = choice([True,True,False])
			game.save()