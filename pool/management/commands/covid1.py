from django.core.management.base import BaseCommand, CommandError
from pool.models import Game,Pick
from django.contrib.auth.models import User
from datetime import datetime


class Command(BaseCommand):

	def handle(self, *args, **options):
		# Pittsburgh v Baltimore changes from week 7 to week 8
		#week 8 game 13 -> week 8, game 14
		game = Game.objects.get(week_number=8,game_number=13)
		game.game_number = 14
		game.save()

		#week 7, game 3 -> week 8, game 13
		game = Game.objects.get(week_number=7,game_number=3)
		game.week_number = 8
		game.game_number = 13
		game.game_date = datetime(2020,11,1,13,0,0)
		game.save()

		# pit v ten change from w4 to w7
		#week 4, game 8 -> week 7, game 3
		game = Game.objects.get(week_number=4,game_number=8)
		game.week_number = 7
		game.game_number = 3
		game.game_date = datetime(2020,10,25,13,0,0)
		game.save()

		#delete week 4, all picks where game = 8
		#week 8, add new default pick for game 14
		for user in User.objects.all():
			p = Pick.objects.get(player=user, week_number=4,game_number=8)
			p.delete()
			pick = Pick(week_number=8, game_number=14, player=user,picked_fav=True)
			pick.save()
