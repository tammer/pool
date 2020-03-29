from django.core.management.base import BaseCommand, CommandError
from pool.models import Pick,Game,Monday
from django.contrib.auth.models import User
import random


class Command(BaseCommand):
	help = 'Load the standard teams'

	def handle(self, *args, **options):
		random.seed(1)
		x = input("This will delete all picks and mondays and load in dummy data.  You sure? [Y/n]")

		if x != 'Y':
			print("Aborting")
			exit()

		Pick.objects.all().delete()
		Monday.objects.all().delete()
		players = ['John','Adel','Andy','Madelyn','Mike','David','Feldman','MichaelC','MikeLeroux','Lee','Whiler','Joff','Adam','Ivan','Tristan','Snow','MikeK','Steve','Ethan','Jason','Mark','Dustan','Warren','Karsten','Jeff']
		for username in players:
			(user,created) = User.objects.get_or_create(username=username)
			print(f'{user.username}: {created}')
			for g in Game.objects.all():
				pick = Pick(player=user, week_number = g.week_number,
					game_number = g.game_number, picked_fav = random.choice([True,False]))
				pick.save(force=True)
				# print(f'{pick.week_number},{pick.game_number}')
			for week_number in range(1,9):
				total_points = random.choice(range(30,55))
				monday = Monday(player=user,week_number=week_number,total_points = total_points)
				monday.save(force=True)
		print (f'Total Pick objects: {Pick.objects.all().count()}')
		print (f'Total players: {len(players)}')
		print (f'Total Monday objects: {Monday.objects.all().count()}')


		