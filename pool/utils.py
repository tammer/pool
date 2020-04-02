from pool.models import Team,Game,Pick,Bank,Blog,Monday,now
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta


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

				gm_dt = datetime(int(root[0][i].attrib['eid'][0:4]),
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
	Monday.objects.filter(player=user).delete()
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

def implied_week(now_ = None, delta_hours = 30):
	if now_ is None:
			now_ = now()
	week_number = 1
	last_week_of_season = Game.objects.filter(game_number=1).order_by('week_number').last().week_number
	while week_number < last_week_of_season:
		if now_ < Game.objects.filter(week_number=week_number).order_by('game_date').last().game_date + timedelta(hours=delta_hours):
			return week_number
		else:
			week_number += 1
	return last_week_of_season

def status(now_ = None):
	if now_ is None:
		now_ = now()
	# pre week 1
	if now_ < Game.objects.get(week_number=1,game_number=1).game_date:
		if Game.objects.filter(week_number=1,spread__isnull=True).count() == 0:
			return (1,'Open')
		else:
			return (1, 'Not Open')
	# post week 17
	last_game_of_season = Game.objects.all().order_by('game_date').last()
	if now_ > last_game_of_season.game_date:
		return (last_game_of_season.week_number,'Closed')
	# all other cases
	iw = implied_week(now_,6)
	if now_.weekday() in (3,4,5):
		return (iw,'Open')
	elif now_.weekday() == 6:
		if now_.hour > 12:
			return (iw,'Closed')
		else:
			return (iw,'Open')
	elif now_.weekday() == 0:
		return (iw,'Closed')
	else: # Tues,Wed
		if Game.objects.filter(week_number=iw,spread__isnull=True).count() == 0:
			return (iw,'Open')
		else:
			return (iw, 'Not Open')


# def impliedWeek_by_filled_in_scores():
# 	first_week_without_a_score = Game.objects.filter(fav_score__isnull = True).order_by('week_number').first().week_number
# 	if Game.objects.filter(week_number = first_week_without_a_score, fav_score__isnull = False).order_by('week_number').first().week_number == first_week_without_a_score:
# 		# first_week_without_a_score has nuls and scores.  This must be the week we're in
# 		return first_week_without_a_score
# 	else:
# 		# all scores have been input
# 		if now().weekday() == 6 or now().weekday() == 0:
# 			return first_week_without_a_score - 1 # it's not Tuesday yet
# 		else:
# 			return first_week_without_a_score

def score_matrix():
	matrix = {}
	query = 'SELECT *, auth_user.username as player_name, pool_game.week_number as wk, sum((fav_score-udog_score-spread > 0 and picked_fav OR fav_score-udog_score-spread <0 and not(picked_fav))) as correct FROM pool_pick,pool_game,auth_user WHERE pool_pick.game_number = pool_game.game_number and pool_pick.week_number=pool_game.week_number and pool_pick.player_id = auth_user.id and not(pool_game.fav_score is NULL) GROUP BY player_name, wk;'

	for pick in Pick.objects.raw(query):
		player = pick.player_name
		week_number = pick.week_number
		if not(player in matrix):
			matrix[player] = {}
		matrix[player][week_number] = pick.correct
	return matrix

def dead_list(end=None, sm=None):
	if end is None:
		end = implied_week()
	if sm is None:
		sm = score_matrix()
	if end < 1:
		return set()
	results = set()
	week_number = 1
	if end > len(sm[list(sm.keys())[0]]):
		end = len(sm[list(sm.keys())[0]])
	while week_number < end+1:
		min_score = 99;
		for player, score in sm.items():
			if score[week_number] < min_score and not(player in results):
				min_score = score[week_number]
		for player, score in sm.items():
			if score[week_number] == min_score:
				results.add(player)
		week_number += 1;
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
	dl = dead_list(week_number-1)
	for item in standings:
		dead = False
		if item[0] in dl:
			dead = True
		standings2.append([item[0],int(item[1]),dead])
	return standings2

def whoWon(week_number, score_matrix):
	leaders = []
	best_score = 0
	for player, score in score_matrix.items():
		if score[week_number] > best_score:
			best_score = score[week_number]
			leaders = [player]
		elif score[week_number] == best_score:
			leaders.append(player)
	if best_score == 0:
		return None
	else:
		if len(leaders) == 1:
			return leaders[0]
		else:
			best_bonus = 0
			leader = None
			for player in leaders:
				user = User.objects.get(username=player)
				bonus = Monday.objects.get(player=user, week_number=week_number).bonus()
				if bonus > best_bonus:
					leader = player
					best_bonus = bonus
			return leader



def overall(sm = None):
	if sm is None:
		sm = score_matrix()
	total = {}
	for player, scores in sm.items():
		total[player] = sum(scores.values())
	rank_order = sorted(total.items(), key=lambda kv: kv[1], reverse=True)
	table = []
	winner = []
	for item in rank_order:
		player = item[0]
		this_row = [[player,0]]
		weeks = list(sm[player].keys())
		weeks.sort()
		for week in weeks:
			win = 0
			if whoWon(week,sm) == player:
				win=1
			this_row.append([sm[player][week],win])
		this_row.append([total[player],0])
		table.append(this_row)
	return table
