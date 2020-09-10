from django.core.management.base import BaseCommand, CommandError
from pool.models import Game,now
from pool.utils import load_scores,implied_week
from datetime import datetime, timedelta

class Command(BaseCommand):
	help = 'Pull the latest scores'

	def handle(self, *args, **options):
		this_week = implied_week()
		for g in Game.objects.filter(week_number=this_week):
			expected_end_time = g.game_date + timedelta(hours=2,minutes=45)
			if not(g.isOver()) and now() > expected_end_time:
				print(now().strftime("%m/%d/%Y, %H:%M:%S") + ": CHECKING FOR NEW FINAL SCORES")
				load_scores()
				return
		print(now().strftime("%m/%d/%Y, %H:%M:%S") + ": No games need to be updated at this time")
