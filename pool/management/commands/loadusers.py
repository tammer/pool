from django.core.management.base import BaseCommand, CommandError
from pool.models import Pick,Game
from django.contrib.auth.models import User
from random import choice


class Command(BaseCommand):
	help = 'Load the standard teams'

	def handle(self, *args, **options):
		try:
			user = User.objects.get(username='John')
		except User.DoesNotExist:
			user = User(username='John')
			user.save()
		Pick.objects.filter(player = user).delete()
		for g in Game.objects.all():
			Pick.objects.create(player=user, week_number = g.week_number,
				game_number = g.game_number, picked_fav = choice([True,False]))


		