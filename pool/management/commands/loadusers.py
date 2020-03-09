from django.core.management.base import BaseCommand, CommandError
from pool.models import Pick,Game
from django.contrib.auth.models import User
from random import choice


class Command(BaseCommand):
	help = 'Load the standard teams'

	def handle(self, *args, **options):

		x = input("This will cascade to games, picks, etc.  You sure? [Y/n]")

		if x != 'Y':
			print("Aborting")
			exit()

		for username in ['John','Adel','Andy','Madelyn','Mike','David','Feldman','MichaelC','MikeLeroux','Lee','Whiler','Joff','Adam','Ivan','Tristan','Snow','MikeK','Steve','Ethan','Jason','Mark','Dustan','Warren','Karsten','Jeff']:
			try:
				user = User.objects.get(username=username)
			except User.DoesNotExist:
				user = User(username=username)
				user.save()
			Pick.objects.filter(player = user).delete()
			for g in Game.objects.all():
				Pick.objects.create(player=user, week_number = g.week_number,
					game_number = g.game_number, picked_fav = choice([True,False]))


		