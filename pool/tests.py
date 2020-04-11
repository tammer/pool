# -*- coding: future_fstrings -*-
from django.test import TestCase
from pool.models import Team, Game, Pick, Monday,Main,set_now
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

		m = Main()
		m.now = datetime.datetime(2019,10,18)
		m.save()

		# B2 = User.objects.get(username='B2')
		# for game in Game.objects.filter(week_number=1).order_by('game_number'):
		# 	pick = Pick.objects.get(week_number=1,game_number=game.game_number,player=B2)
		# 	print(f'{game.game_number}: {game.favWins()}, {pick.picked_fav}')


		# x = pool.utils.standings(5)
		# print(f'{x}')


	def test(self):
		x = User.objects.get(username='Tammer')
		self.assertEqual(x.username, 'Tammer')

		# testing results() function
		expected = ([{'fav': 'PACKERS', 'udog': 'eagles', 'fav_score': 18, 'udog_score': 22, 'spread': 3, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Thursday'}, {'fav': 'falcons', 'udog': 'TITANS', 'fav_score': 24, 'udog_score': 21, 'spread': 1, 'right': 'Yes', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'ravens', 'udog': 'BROWNS', 'fav_score': 18, 'udog_score': 30, 'spread': 9, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'bills', 'udog': 'PATRIOTS', 'fav_score': 35, 'udog_score': 21, 'spread': 3, 'right': 'Yes', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'lions', 'udog': 'CHIEFS', 'fav_score': 24, 'udog_score': 14, 'spread': 3, 'right': 'Yes', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'texans', 'udog': 'PANTHERS', 'fav_score': 18, 'udog_score': 20, 'spread': 4, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'COLTS', 'udog': 'raiders', 'fav_score': 30, 'udog_score': 20, 'spread': 3, 'right': 'Yes', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'DOLPHINS', 'udog': 'chargers', 'fav_score': 22, 'udog_score': 24, 'spread': 3, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'giants', 'udog': 'REDSKINS', 'fav_score': 24, 'udog_score': 14, 'spread': 3, 'right': 'Yes', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'CARDINALS', 'udog': 'seahawks', 'fav_score': 24, 'udog_score': 30, 'spread': 3, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'rams', 'udog': 'BUCCANEERS', 'fav_score': 30, 'udog_score': 30, 'spread': 1, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'BEARS', 'udog': 'vikings', 'fav_score': 33, 'udog_score': 30, 'spread': 6, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'BRONCOS', 'udog': 'jaguars', 'fav_score': 30, 'udog_score': 32, 'spread': 1, 'right': 'No', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'SAINTS', 'udog': 'cowboys', 'fav_score': 33, 'udog_score': 14, 'spread': 2, 'right': 'Yes', 'picked_fav': True, 'isOver': True, 'game_day': 'Sunday'}, {'fav': 'STEELERS', 'udog': 'bengals', 'fav_score': 22, 'udog_score': 14, 'spread': 3, 'right': 'Yes', 'picked_fav': True, 'isOver': True, 'game_day': 'Monday'}], 7, 15, 15)
		self.assertEqual(pool.utils.results(4,'Tammer'),expected)

		# testing all_picks() function
		expected = {'Adel': ['ten', 'CIN', 'DAL', 'DEN', 'IND', 'BAL', 'MIN', 'nyj', 'PHI', 'ARI', 'tb', 'HOU', 'SEA', 'SF', 'CLE', 'CHI', 51], 'B1': ['ten', 'buf', 'mia', 'gb', 'atl', 'BAL', 'oak', 'NE', 'det', 'car', 'NYG', 'lac', 'SEA', 'SF', 'la', 'was', 36], 'B2': ['JAX', 'CIN', 'DAL', 'gb', 'IND', 'BAL', 'oak', 'nyj', 'PHI', 'car', 'NYG', 'lac', 'SEA', 'pit', 'CLE', 'was', 33], 'John': ['ten', 'buf', 'DAL', 'DEN', 'IND', 'BAL', 'oak', 'NE', 'det', 'car', 'NYG', 'HOU', 'no', 'SF', 'la', 'CHI', 37], 'Tammer': ['ten', 'buf', 'DAL', 'DEN', 'atl', 'kc', 'oak', 'NE', 'PHI', 'car', 'tb', 'HOU', 'no', 'SF', 'la', 'CHI', 46]}
		self.assertEqual(pool.utils.all_picks(3,True), expected)

		# pool.utils.all_picks(7,False)

		# testing set_score() function
		gm = Game.objects.get(week_number=2,game_number=2)
		pool.utils.set_score(gm.week_number,{gm.favShortName():55,gm.udogShortName().lower():5})
		gm = Game.objects.get(week_number=2,game_number=2)
		self.assertEqual(gm.udog_score,5)
		self.assertEqual(gm.fav_score,55)

		self.assertRaises(NameError, pool.utils.set_score, 1,{'notateam':55,'SF':5})
		self.assertRaises(NameError, pool.utils.set_score, 1,{'DAL':55,'ne':5})

		# testing status() function

		self.assertEqual(pool.utils.status(datetime.datetime(2019,8,8)), (1,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,5)), (1,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,6)), (1,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,7)), (1,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,8,12,59)), (1,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,8,13,0)), (1,'Closed'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,9,13,0)), (1,'Closed'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,10,13,0)), (2,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,11,13,0)), (2,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,12,13,0)), (2,'Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,9,12,13,0)), (2,'Open'))

		self.assertEqual(pool.utils.status(datetime.datetime(2019,10,23,13,0)), (8,'Not Open'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,10,28,13,0)), (8,'Closed'))
		self.assertEqual(pool.utils.status(datetime.datetime(2019,10,29,13,0)), (9,'Not Open'))

		self.assertEqual(pool.utils.status(datetime.datetime(2019,12,31,13,0)), (17,'Closed'))		
		self.assertEqual(pool.utils.status(datetime.datetime(2020,2,2,13,0)), (17,'Closed'))		




		# testing standings() function

		x = pool.utils.standings(1,False)
		y = "[['John', 8, False], ['B1', 8, False], ['B2', 8, False], ['Tammer', 6, False], ['Adel', 4, False]]"
		self.assertEqual(f'{x}',y)
		x = pool.utils.standings(2,False)
		y = "[['Adel', 11, True], ['B1', 9, False], ['B2', 9, False], ['Tammer', 9, False], ['John', 7, False]]"
		self.assertEqual(f'{x}',y)
		x = pool.utils.standings(3,False)
		y = "[['Tammer', 12, False], ['John', 10, True], ['B2', 8, False], ['Adel', 8, True], ['B1', 6, False]]"
		self.assertEqual(f'{x}',y,False)
		x = pool.utils.standings(4,False)
		y = "[['B1', 7, True], ['B2', 7, False], ['Tammer', 7, False], ['Adel', 7, True], ['John', 7, True]]"
		self.assertEqual(f'{x}',y)
		x = pool.utils.standings(5,False)
		y = [['Adel', 0, True], ['B1', 0, True], ['B2', 0, True], ['John', 0, True],['Tammer', 0, True]]
		self.assertEqual(x,y)


		# Testing dead_list()

		sm = {'John': {1: 6, 2: 9, 3: 1, 4: 6, 5: 8, 6: 10, 7: 5}, 'Adel': {1: 13, 2: 9, 3: 4, 4: 11, 5: 6, 6: 5, 7: 5}, 'Andy': {1: 7, 2: 8, 3: 5, 4: 9, 5: 11, 6: 5, 7: 6}, 'Madelyn': {1: 9, 2: 9, 3: 7, 4: 7, 5: 9, 6: 7, 7: 8}}


		x = pool.utils.dead_list(end=1,sm=sm)
		y = "{'John'}"
		self.assertEqual(f'{x}',y)

		x = pool.utils.dead_list(end=2,sm=sm)
		y = {'John', 'Andy'}
		self.assertEqual(x,y)

		x = pool.utils.dead_list(end=3,sm=sm)
		y = {'Andy', 'John', 'Adel'}
		self.assertEqual(x,y)

		x = pool.utils.dead_list(end=4,sm=sm)
		y = {'Andy', 'John', 'Adel', 'Madelyn'}
		self.assertEqual(x,y)		

		y = pool.utils.dead_list(end=13,sm=sm) # beyond the end of the sm
		y = {'Andy', 'John', 'Adel', 'Madelyn'}
		self.assertEqual(x,y)

		# testing overall()

		user_b1 = User.objects.get(username='B1')
		user_adel = User.objects.get(username='Adel')
		user_john = User.objects.get(username='John')
		sm = {'John': {1: 6, 2: 9, 3: 1, 4: 6, 5: 8, 6: 10, 7: 5}, 'Adel': {1: 13, 2: 9, 3: 4, 4: 11, 5: 6, 6: 5, 7: 5}, 'Tammer': {1: 7, 2: 8, 3: 5, 4: 9, 5: 11, 6: 5, 7: 6}, 'B1': {1: 9, 2: 9, 3: 7, 4: 7, 5: 9, 6: 7, 7: 8}}
		x = pool.utils.overall(sm)
		y = [[['B1', 0], [9, 0], [9, 0], [7, 1], [7, 0], [9, 0], [7, 0], [8, 1], [56, 0]], [['Adel', 0], [13, 1], [9, 1], [4, 0], [11, 1], [6, 0], [5, 0], [5, 0], [53, 0]], [['Tammer', 0], [7, 0], [8, 0], [5, 0], [9, 0], [11, 1], [5, 0], [6, 0], [51, 0]], [['John', 0], [6, 0], [9, 0], [1, 0], [6, 0], [8, 0], [10, 1], [5, 0], [45, 0]]]
		self.assertEqual(x,y)

		set_now(datetime.datetime(2019,9,6,13,21))
		x = pool.utils.all_picks(1)
		expected = {'Adel': ['chi', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 'B1': ['chi', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 'B2': ['chi', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 'John': ['chi', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''], 'Tammer': ['chi', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']}
		self.assertEqual(x,expected)



class GameTestCase(TestCase):
	def setUp(self):

		m = Main()
		m.now = datetime.datetime(2019,10,18)
		m.save()

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






