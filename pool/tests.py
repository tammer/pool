from django.test import TestCase
from pool.models import Team, Game, Pick, Monday
from django.contrib.auth.models import User
import requests, csv
import datetime
from pytz import timezone


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

		game_date = datetime.datetime(2020,12,31,tzinfo=timezone('US/Eastern'))
		Game.objects.create(week_number=1, game_number=1, fav = Team.objects.get(short_name='NYG'),
				udog = Team.objects.get(short_name='DAL'), spread = 11.5,
				game_date = game_date, fav_is_home = True,
				fav_score=33, udog_score=21, is_final = True)

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
		x.game_date = datetime.datetime(2020,3,1,16,0,0,tzinfo=timezone('US/Eastern'))
		current_time = datetime.datetime(2020,3,1,11,0,0,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), False)
		current_time = datetime.datetime(2020,3,1,14,0,0,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), True)

		# Saturday game.  Should be closed only if after kick off
		x.game_date = datetime.datetime(2020,2,29,16,0,0,tzinfo=timezone('US/Eastern'))
		current_time = datetime.datetime(2020,2,29,15,59,59,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), False)
		current_time = datetime.datetime(2020,2,29,16,0,1,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), True)

		# Monday game, should be closed as long as it's after 1pm sunday
		x.game_date = datetime.datetime(2020,3,2,21,0,0,tzinfo=timezone('US/Eastern'))
		current_time = datetime.datetime(2020,3,1,15,59,59,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), True)
		current_time = datetime.datetime(2020,3,1,11,59,59,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), False)
		self.assertEqual(x.isOpen(current_time=current_time), True)
		current_time = datetime.datetime(2020,3,2,11,59,59,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), True)
		current_time = datetime.datetime(2020,3,3,11,59,59,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), True)

		# Sunday 9a game should be open until kick off
		x.game_date = datetime.datetime(2020,3,1,9,0,0,tzinfo=timezone('US/Eastern'))
		current_time = datetime.datetime(2020,3,1,8,0,0,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), False)
		current_time = datetime.datetime(2020,3,1,10,0,0,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(current_time=current_time), True)
		self.assertEqual(x.isOpen(current_time=current_time), False)

		# Now one check with not setting current_time
		x.game_date = datetime.datetime(1971,3,1,9,0,0,tzinfo=timezone('US/Eastern'))
		self.assertEqual(x.isClosed(), True)


		user = User.objects.get(username='Tammer')
		x = Pick.objects.get(player=user,week_number=1,game_number=1)
		g = Game.objects.get(week_number=1,game_number=1)
		self.assertEqual(x.picked_fav, True)
		self.assertEqual(x.isCorrect(), g.fav_score - g.udog_score > g.spread)






