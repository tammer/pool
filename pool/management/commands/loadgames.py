from django.core.management.base import BaseCommand, CommandError
from pool.models import Team,Game
import requests
import csv
import datetime

class Command(BaseCommand):
	help = 'Load games'

	def handle(self, *args, **options):
		x = input("This will cascade.  You sure? [Y/n]")
		# x = 'Y'
		if( x != 'Y' ):
			self.stdout.write("Aborting")
		else:
			Game.objects.all().delete()
			Game(week_number=1, game_number=1, fav = Team.objects.filter(short_name='NYG').first(),
				udog = Team.objects.filter(short_name='DAL').first(), spread = 11.5,
				game_date = datetime.datetime.now(), fav_is_home = True,
				fav_score=33, udog_score=21).save()

			Game(week_number=1, game_number=2, fav = Team.objects.filter(short_name='CLE').first(),
				udog = Team.objects.filter(short_name='TB').first(), spread = 5.5,
				game_date = datetime.datetime.now(), fav_is_home = True).save()

			Game(week_number=1, game_number=3, fav = Team.objects.filter(short_name='NE').first(),
				udog = Team.objects.filter(short_name='MIA').first(), spread = 2.5,
				game_date = datetime.datetime.now(), fav_is_home = True).save()

			Game(week_number=1, game_number=4, fav = Team.objects.filter(short_name='HOU').first(),
				udog = Team.objects.filter(short_name='SF').first(), spread = 1.5,
				game_date = datetime.datetime.now(), fav_is_home = True).save()

