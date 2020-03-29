from pool.models import Team,Game,Pick,Bank,Blog,Monday,now
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import requests
import xml.etree.ElementTree as ET
import datetime
import csv

def load_teams():
	Team.objects.all().delete()
	url = 'https://gist.githubusercontent.com/tammer/b5cfda38c1ea1062d2197675bcf8b220/raw/2d77403b87c21caff2bc48f3cddf1f2270c2c041/nfl_teams.csv'
	response = requests.get(url)
	if response.status_code != 200:
		print('Failed to get data:', response.status_code)
	else:
		wrapper = list(csv.reader(response.text.strip().split('\n')))
		wrapper.pop(0)
		for record in wrapper:
			# print(record)
			nn = record[1].split(' ')[-1]
			cn = record[1].replace(' '+nn,'')
			if cn == 'NY':
				cn = 'New York'
			elif cn == 'LA':
				cn = 'Los Angeles'
			Team(full_name = record[1], short_name = record[2], nick_name=nn, city_name=cn).save()

def load_games(this_year):
	Game.objects.all().delete()
	for x in range(17):
		week_number = x+1
		url = 'http://www.nfl.com/ajax/scorestrip?season='+str(this_year)+'&seasonType=REG&week='+str(week_number)
		response = requests.get(url)
		if response.status_code != 200:
			print('Failed to get data:', response.status_code)
		else:
			root = ET.fromstring(response.text)
			i=0
			for gm in root[0]:
				
				# print(gm.attrib)
				hour = int(root[0][i].attrib['t'].split(':')[0])
				if hour < 12:
					hour += 12 # !!! Totally fails if the game is actually in the morning

				gm_dt = datetime.datetime(int(root[0][i].attrib['eid'][0:4]),
					int(root[0][i].attrib['eid'][4:6]),
					int(root[0][i].attrib['eid'][6:8]),
					hour,
					int(root[0][i].attrib['t'].split(':')[1])
					)
				
				Game.objects.create(
					week_number = week_number, game_number=i+1,
					fav = Team.objects.get(short_name=gm.attrib['h']),
					udog = Team.objects.get(short_name=gm.attrib['v']),
					game_date = gm_dt,
					fav_is_home = True)
				i=i+1


def add_player(username,email,pw):
	if User.objects.filter(username=username).exists():
		raise( NameError(f'{username} exists already'))
	User.objects.create_user(username,email,pw)
	init_player(username)

# This function assumes games are loaded
def init_player(username):
	user = User.objects.get(username=username)
	Pick.objects.filter(player=user).delete()
	for game in Game.objects.all():
		pick = Pick(week_number=game.week_number, game_number=game.game_number, player=user,picked_fav=True)
		pick.save(force=True)
	for game in Game.objects.filter(game_number=1):
		monday = Monday(week_number=game.week_number,player=user,total_points=0)
		monday.save(force=True)

def delete_player(username):
	if not(User.objects.filter(username=username).exists()):
		raise( NameError(f'{username} does not exist'))
	user = User.objects.get(username=username)
	Monday.objects.filter(player=user).delete()
	Pick.objects.filter(player=user).delete()
	user.delete()

def score_matrix():
	matrix = {}
	query = 'SELECT *, \
	(fav_score-udog_score-spread > 0 and picked_fav OR fav_score-udog_score-spread <0 and not(picked_fav)) as correct, \
	auth_user.username as player_name\
	from pool_pick,pool_game,auth_user \
	where pool_pick.game_number = pool_game.game_number and \
	      pool_pick.week_number=pool_game.week_number and \
	      pool_pick.player_id = auth_user.id and\
	      not(pool_game.fav_score is NULL)'

	for pick in Pick.objects.raw(query):
		player = pick.player_name
		week_number = pick.week_number
		if not(player in matrix):
			matrix[player] = {}
		if not(week_number in matrix[player]):
			matrix[player][week_number] = 0
		if pick.correct:
			matrix[player][week_number] += 1
	return matrix

def dead_list(start=1, end=None):
	week_number = end
	if week_number is None:
		week_number = implied_week()
	sm = score_matrix()
	results = set()
	while week_number > start-1:
		min_score = 99;
		for player, score in sm.items():
			if score[week_number] < min_score:
				min_score = score[week_number]
		for player, score in sm.items():
			if score[week_number] == min_score:
				results.add(player)
		week_number -= 1;
	return results

def standings(week_number):
	matrix = {}
	for user in User.objects.all():
		count = 0;
		for pick in Pick.objects.filter(player=user,week_number=week_number):
			if pick.isCorrect():
				count +=1
		try:
			count += Monday.objects.get(week_number=week_number,player=user).bonus()
		except:
			None
		matrix[user.username] = count
		standings = sorted(matrix.items(), key=lambda kv: kv[1], reverse=True)
	standings2 = []
	dl = dead_list(1,week_number-1)
	for item in standings:
		dead = False
		if item[0] in dl:
			dead = True
		standings2.append([item[0],int(item[1]),dead])
	return standings2
