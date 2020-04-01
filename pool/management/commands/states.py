from django.core.management.base import BaseCommand, CommandError
from pool.models import Team,Game,Pick
import random
from datetime import datetime, timedelta

dates = [
	(2019,8,18,13,21,0), # Preseason
	(2019,10,18,13,21,0), # Friday 13:21
	(2019,10,20,13,21,0), # Sunday 13:21
	(2019,10,21,13,21,0), # Monday 13:21
	(2019,10,22,13,21,0), # Tuesday 13:21
	(2019,10,23,13,21,0), # Wednesday 13:21
	(2019,10,24,13,21,0), # Thursday 13:21
	(2019,10,24,20,21,0), 
	(2019,12,28,20,21,0), 
	(2020,1,12,10,21,0), 
]

def give_picks(week_number):
	for pick in Pick.objects.filter(week_number=week_number):
		pick.picked_fav = random.choice([True,False])
		pick.save(force=True)

def set_state(date):
	# fill in spreads and scores
	random.seed(1)
	spread_week = 1
	give_picks(spread_week)
	while spread_week <= 17 and date > (Game.objects.filter(week_number=spread_week).order_by('game_number').first().game_date - timedelta(hours=60)):
		spread_week +=1
		give_picks(spread_week)
	for game in Game.objects.all().order_by('game_date'):
		if( game.week_number <= spread_week ):
			game.spread = random.choice([0,1,1,2,2,2,3,3,3,3,4,4,5,6,6,7,9,10])
			if( game.game_date < date - timedelta(hours=3)):
				game.fav_score = random.choice([24,22,24,30,28,35,18,22,35,33])
				game.udog_score = random.choice([20,20,22,28,24,32,14,21,30,30])
			else:
				game.fav_score = None
				game.udog_score = None
		else:
			game.fav_score = None
			game.udog_score = None
			game.spread = None
		game.save()

class Command(BaseCommand):
	help = 'Run through various chronological db states'

	def handle(self, *args, **options):
		for date in dates:
			date = datetime(*date)
			set_state(date)
			text_file = open("now.txt", "w")
			text_file.write(f'{date.year},{date.month},{date.day},{date.hour},{date.minute},{date.second}')
			text_file.close()
			print(f'State set to: {date} Next?')
			if input() == 'n':
				exit()

