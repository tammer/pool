from django.test import TestCase
from pool.models import Team, Game, Pick, Monday
from django.contrib.auth.models import User
import requests, csv
import datetime
from pytz import timezone
import pool.utils
import random


class UtilTestCase(TestCase):
	def setUp(self):
		random.seed(1)
		pool.utils.load_teams()
		pool.utils.load_games(2019)
		pool.utils.add_player("Tammer","tammer@tammer.com",'123')
		pool.utils.add_player("John","j@tammer.com",'123')
		pool.utils.add_player("Adel","akamel@tammer.com",'123')
		pool.utils.add_player("B1","b1@tammer.com",'123')
		pool.utils.add_player("B2","b2@tammer.com",'123')
		
		for user in User.objects.all():
			for g in Game.objects.filter(week_number__lte = 3):
				pick = Pick.objects.get(player=user, week_number = g.week_number, game_number = g.game_number)
				pick.picked_fav = random.choice([True,False])
				pick.save(force=True)
			for week_number in range(1,5):
				total_points = random.choice(range(30,55))
				monday = Monday.objects.get(player=user,week_number=week_number)
				monday.total_points = total_points
				monday.save(force=True)

		random.seed(1)
		for game in Game.objects.all():
			if game.week_number < 5:
				game.spread = random.choice([0,1,1,2,2,2,3,3,3,3,4,4,5,6,6,7,9,10])
				game.fav_is_home = random.choice([True,True,False])
				if game.week_number < 5 or game.game_number < 10:
					game.fav_score = random.choice([24,22,24,30,28,35,18,22,35,33])
					game.udog_score = random.choice([20,20,22,28,24,32,14,21,30,30])
			game.save()

		# B2 = User.objects.get(username='B2')
		# for game in Game.objects.filter(week_number=1).order_by('game_number'):
		# 	pick = Pick.objects.get(week_number=1,game_number=game.game_number,player=B2)
		# 	print(f'{game.game_number}: {game.favWins()}, {pick.picked_fav}')


		# x = pool.utils.standings(5)
		# print(f'{x}')


	def test(self):
		x = User.objects.get(username='Tammer')
		self.assertEqual(x.username, 'Tammer')
		x = pool.utils.standings(1)
		y = "[['John', 8, False], ['B1', 8, False], ['B2', 8, False], ['Tammer', 6, False], ['Adel', 4, False]]"
		self.assertEqual(f'{x}',y)
		x = pool.utils.standings(2)
		y = "[['Adel', 11, True], ['Tammer', 9, False], ['B1', 9, False], ['B2', 9, False], ['John', 7, False]]"
		self.assertEqual(f'{x}',y)
		x = pool.utils.standings(3)
		y = "[['Tammer', 12, False], ['John', 10, True], ['B2', 8, False], ['Adel', 8, True], ['B1', 6, False]]"
		self.assertEqual(f'{x}',y)
		x = pool.utils.standings(4)
		y = "[['B1', 7, True], ['B2', 7, False], ['Tammer', 7, False], ['Adel', 7, True], ['John', 7, True]]"
		self.assertEqual(f'{x}',y)
		x = pool.utils.standings(5)
		y = "[['Tammer', 0, True], ['John', 0, True], ['Adel', 0, True], ['B1', 0, True], ['B2', 0, True]]"
		self.assertEqual(f'{x}',y)

class GameTestCase(TestCase):
	def setUp(self):

		# Create a user

		User.objects.create_user(username='Tammer', password='12345')

		# Create some teams

		url = 'https://gist.githubusercontent.com/tammer/b5cfda38c1ea1062d2197675bcf8b220/raw/3d24741414781e11a50a0c25bfc0b04cc35fc0f0/nfl_teams.csv'
		response = requests.get(url)
		if response.status_code != 200:
			print('Failed to get data:', response.status_code)
			exit()
		wrapper = list(csv.reader(response.text.strip().split('\n')))
		wrapper.pop(0)
		for record in wrapper:
			nn = record[1].split(' ')[-1]
			cn = record[1].replace(' '+nn,'')
			if cn == 'NY':
				cn = 'New York'
			elif cn == 'LA':
				cn = 'Los Angeles'
			Team.objects.create(full_name = record[1], short_name = record[2], nick_name=nn, city_name=cn)

		# Create a game

		game_date = datetime.datetime(2020,12,31)
		Game.objects.create(week_number=1, game_number=1, fav = Team.objects.get(short_name='NYG'),
				udog = Team.objects.get(short_name='DAL'), spread = 11.5,
				game_date = game_date, fav_is_home = True,
				fav_score=33, udog_score=21)

		# Create a pick

		Pick.objects.create(player=User.objects.get(username='Tammer'), week_number=1,game_number=1,picked_fav=True)

	def test(self):
		"""Sanity Checks on Team, Game, Pick"""
		x = Team.objects.get(short_name='SF')
		self.assertEqual(x.nick_name, '49ers')

		x = Game.objects.get(week_number=1,game_number=1)
		x.fav_score = 21
		x.udog_score = 14
		x.spread = 5
		self.assertEqual(x.favWins(), True)
		x.spread = 10
		self.assertEqual(x.favWins(), False)

		# Sunday game at 4pm should be open if time before 1 else closed
		x.game_date = datetime.datetime(2020,3,1,16,0,0)
		current_time = datetime.datetime(2020,3,1,11,0,0)
		self.assertEqual(x.isClosed(current_time=current_time), False)
		current_time = datetime.datetime(2020,3,1,14,0,0)
		self.assertEqual(x.isClosed(current_time=current_time), True)

		# Saturday game.  Should be closed only if after kick off
		x.game_date = datetime.datetime(2020,2,29,16,0,0)
		current_time = datetime.datetime(2020,2,29,15,59,59)
		self.assertEqual(x.isClosed(current_time=current_time), False)
		current_time = datetime.datetime(2020,2,29,16,0,1)
		self.assertEqual(x.isClosed(current_time=current_time), True)

		# Monday game, should be closed as long as it's after 1pm sunday
		x.game_date = datetime.datetime(2020,3,2,21,0,0)
		current_time = datetime.datetime(2020,3,1,15,59,59)
		self.assertEqual(x.isClosed(current_time=current_time), True)
		current_time = datetime.datetime(2020,3,1,11,59,59)
		self.assertEqual(x.isClosed(current_time=current_time), False)
		self.assertEqual(x.isOpen(current_time=current_time), True)
		current_time = datetime.datetime(2020,3,2,11,59,59)
		self.assertEqual(x.isClosed(current_time=current_time), True)
		current_time = datetime.datetime(2020,3,3,11,59,59)
		self.assertEqual(x.isClosed(current_time=current_time), True)

		# Sunday 9a game should be open until kick off
		x.game_date = datetime.datetime(2020,3,1,9,0,0)
		current_time = datetime.datetime(2020,3,1,8,0,0)
		self.assertEqual(x.isClosed(current_time=current_time), False)
		current_time = datetime.datetime(2020,3,1,10,0,0)
		self.assertEqual(x.isClosed(current_time=current_time), True)
		self.assertEqual(x.isOpen(current_time=current_time), False)

		# Now one check with not setting current_time
		x.game_date = datetime.datetime(1971,3,1,9,0,0)
		self.assertEqual(x.isClosed(), True)


		user = User.objects.get(username='Tammer')
		x = Pick.objects.get(player=user,week_number=1,game_number=1)
		g = Game.objects.get(week_number=1,game_number=1)
		self.assertEqual(x.picked_fav, True)
		self.assertEqual(x.isCorrect(), g.fav_score - g.udog_score > g.spread)






