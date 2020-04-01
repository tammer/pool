from django.core.management.base import BaseCommand, CommandError
from pool.models import Pick,Game,Monday
from django.contrib.auth.models import User
from pool.utils import init_player
import random


class Command(BaseCommand):
	help = 'Load the standard teams'

	def handle(self, *args, **options):
		random.seed(1)
		x = input("This will delete all picks and mondays and load in defaults (all favs).  You sure? [Y/n]")

		if x != 'Y':
			print("Aborting")
			exit()

		players = ['John','Adel','Andy','Madelyn','Mike','David','Feldman','MichaelC','MikeLeroux','Lee','Whiler','Joff','Adam','Ivan','Tristan','Snow','MikeK','Steve','Ethan','Jason','Mark','Dustan','Warren','Karsten','Jeff']
		for username in players:
			(user,created) = User.objects.get_or_create(username=username)
			print(f'{user.username}: {created}')
			init_player(username)


		