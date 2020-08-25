from django.core.management.base import BaseCommand, CommandError
from pool.models import Team,Game
from pool.utils import load_games, load_teams, init_all_users
from datetime import datetime

class Command(BaseCommand):
	help = 'Init the season'

	def handle(self, *args, **options):
		this_year = datetime.now().year
		y = input("This operation will destroy all teams, games, picks, setting up for year " + str(this_year) + "  Proceed? Y/n? ")
		if y == 'Y':
			load_teams()
			print("Teams loaded")
			load_games(this_year)
			print("Games loaded")
			init_all_users()
			print("Default picks done for all users")
			print("First Game of Season:")
			gm = Game.objects.get(week_number=1,game_number=1)
			print(gm.game_date.strftime('%A %d-%b-%Y %H:%M:%S'))
			print(gm.udog.nick_name + " at " + gm.fav.city_name)
			print("Total Games: " + str(Game.objects.count()))