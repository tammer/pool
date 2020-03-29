from django.core.management.base import BaseCommand, CommandError
from pool.models import Team,Game
import random

class Command(BaseCommand):
	help = 'Load some spreads and scores into existing games (for testing)'

	def handle(self, *args, **options):

		x = input("This will put dummy scores in Games.  You sure? [Y/n]")

		if x != 'Y':
			print("Aborting")
			exit()


		random.seed(1)
		for game in Game.objects.all():
			if game.week_number < 8:
				game.spread = random.choice([0,1,1,2,2,2,3,3,3,3,4,4,5,6,6,7,9,10])
				game.fav_is_home = random.choice([True,True,False])
				if game.week_number < 9 or game.game_number < 10:
					game.fav_score = random.choice([24,22,24,30,28,35,18,22,35,33])
					game.udog_score = random.choice([20,20,22,28,24,32,14,21,30,30])
			game.save()

		print("OK, done.")