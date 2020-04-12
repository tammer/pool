# -*- coding: future_fstrings -*-
from pool.models import Team,Game,Pick,Bank,Blog,Monday,now,Main
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta
import random
from django.core import serializers
from os import mkdir

# assumes table is empty. if it is not, you need to delete() it first
def restore(filename):
	f = open(filename, "r")
	data = f.read()
	for obj in serializers.deserialize("json", data):
		obj.save()

def backup():
		tables = ['Team','Game','Pick','Bank','Monday']
		dir_name = datetime.now().strftime('%y-%m-%d-%H-%M')
		path = 'backups/'+dir_name
		mkdir(path)
		for table in tables:
			model = globals()[table]
			data = serializers.serialize("json", model.objects.all())
			fn = path + '/' + table + '.json'
			f = open(fn, "w")
			f.write(data)
			f.close()


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


def set_now(y,m,d,h,s):
	n = datetime(y,m,d,h,s)
	m = Main.objects.first()
	m.now = n
	m.save()
	set_state(m.now)


def results(week_number,player):
	games = []
	right = 0
	total = 0
	completed = 0;
	query = f'SELECT *, pool_pick.picked_fav as picked_fav, (fav_score-udog_score-spread > 0 and picked_fav OR fav_score-udog_score-spread <=0 and not(picked_fav)) as is_correct, pool_team.nick_name as fav_nick_name, pt.nick_name as udog_nick_name FROM pool_game, pool_pick,pool_team, pool_team as pt, auth_user WHERE pool_pick.player_id = auth_user.id and pool_game.week_number = pool_pick.week_number and pool_game.game_number = pool_pick.game_number and pool_game.fav_id = pool_team.id and pool_game.udog_id = pt.id and pool_pick.week_number={week_number} and auth_user.username = "{player}" ORDER BY pool_game.game_number;'
	for game in Game.objects.raw(query):
		total+=1
		if game.isOpen():
			continue
		g = {}
		if game.fav_is_home:
			g['fav'] = game.fav_nick_name.upper()
			g['udog'] = game.udog_nick_name.lower()
		else:
			g['fav'] = game.fav_nick_name.lower()
			g['udog'] = game.udog_nick_name.upper()
		g['fav_score'] = game.fav_score
		g['udog_score'] = game.udog_score
		if game.spread is None:
			g['spread'] = 'NA'
		else:
			g['spread'] = game.spread
		if g['spread'] == 0:
			g['spread'] = ''
		if game.is_correct:
			g['right'] = "Yes"
			right += 1
		else:
			g['right'] = "No"
		if game.isOver():
			completed += 1
		g['picked_fav'] = game.picked_fav
		g['isOver'] = game.isOver()
		g['game_day'] = game.game_date.strftime('%A')
		games.append(g)
	return (games,right,total,completed)





def all_picks(week_number,show_all=False):
	closed = []
	monday_ok_to_show = True
	for game in Game.objects.filter(week_number=week_number):
		if game.isClosed():
			closed.append(game.game_number)
		else:
			monday_ok_to_show = False
	
	matrix = {}
	query = f'SELECT *,auth_user.username as player_name, pool_team.short_name as fav_short_name, pt.short_name as udog_short_name, fav_is_home as fav_is_home FROM pool_team as pt, pool_team, pool_game, pool_pick,auth_user WHERE pt.id = pool_game.udog_id and pool_team.id = pool_game.fav_id and pool_game.game_number = pool_pick.game_number and pool_pick.week_number=pool_game.week_number and pool_pick.player_id = auth_user.id and pool_pick.week_number={week_number} order by player_name, pool_pick.game_number DESC;'
	for pick in Pick.objects.raw(query):

		if not(pick.player_name in matrix):
			if show_all or monday_ok_to_show:
				try:
					tp = Monday.objects.get(week_number=week_number,player=pick.player).total_points
					if tp is None:
						tp = ''
				except:
					tp = ''
			else:
				tp = ''
			matrix[pick.player_name] =[tp]

		if show_all or pick.game_number in closed:
			if pick.picked_fav:
				choice = pick.fav_short_name
				if not(pick.fav_is_home):
					choice = choice.lower()
			else:
				choice = pick.udog_short_name
				if pick.fav_is_home:
					choice = choice.lower()
			matrix[pick.player_name].insert(0,choice)
		else:
			matrix[pick.player_name].insert(0,'')
	return matrix

# score in the form {'dal':22, 'sf':14}
def set_score(week_number, score_):
	score = {}
	for k in score_.keys():
		score[k.upper()] = score_[k]
	try:
		udog = Team.objects.get(short_name = list(score.keys())[0])
		fav = Team.objects.get(short_name = list(score.keys())[1])
	except:
		msg = f'Cannot find a team matching either {list(score.keys())[0]} or {list(score.keys())[1]}'
		raise( NameError(msg) )
	try:
		game = Game.objects.get(week_number=week_number,fav=fav, udog=udog)
	except:
		temp = udog
		udog = fav
		fav = temp
	try:
		game = Game.objects.get(week_number=week_number,fav=fav, udog=udog)
	except:
		msg = f'{fav.short_name} is not playing {udog.short_name} in week {week_number}'
		raise( NameError(msg) )
	game.fav_score = score[fav.short_name]
	game.udog_score = score[udog.short_name]
	game.save()
	return game

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
	iw = implied_week(now_,0)
	if now_.weekday() in (3,4,5):
		return (iw,'Open')
	elif now_.weekday() == 6:
		if now_.hour > 12:
			return (iw,'Closed')
		else:
			return (iw,'Open')
	elif now_.weekday() == 0:
		iw = implied_week(now_,24)
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

def score_matrix(yes_monkey=True):
	matrix = {}
	query = 'SELECT *, auth_user.username as player_name, pool_game.week_number as wk, sum((fav_score-udog_score-spread > 0 and picked_fav OR fav_score-udog_score-spread <=0 and not(picked_fav))) as correct FROM pool_pick,pool_game,auth_user WHERE pool_pick.game_number = pool_game.game_number and pool_pick.week_number=pool_game.week_number and pool_pick.player_id = auth_user.id and not(pool_game.fav_score is NULL) GROUP BY player_name, wk;'

	for pick in Pick.objects.raw(query):
		player = pick.player_name
		week_number = pick.week_number
		if not(player in matrix):
			matrix[player] = {}
		matrix[player][week_number] = int(pick.correct) # production issue, has to integerized
	if yes_monkey == True and matrix != {}:
		matrix['Monkey'] = monkey()
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
			if player == 'Monkey':
				continue
			if score[week_number] < min_score and not(player in results):
				min_score = score[week_number]
		for player, score in sm.items():
			if score[week_number] == min_score:
				results.add(player)
		week_number += 1;
	return results

def monkey():
	completed_games = Game.objects.filter(fav_score__isnull = False).count()
	num_weeks = implied_week()
	completed_games_this_week = Game.objects.filter(week_number=num_weeks, fav_score__isnull = False).count()
	if num_weeks == 1:
		return {1:int(completed_games_this_week/2 + 0.5)}
	scores = {}
	v = []
	ttl = 0
	# random.seed(1)
	while len(v) < num_weeks - 1:
		s = 1+random.random()
		v.append(s)
		ttl += s
	scores[num_weeks] = int(completed_games_this_week / 2 + 0.5)
	total_score = scores[num_weeks]
	while len(v) > 1:
		score = int(completed_games/2 * v.pop() / ttl)
		scores[1+len(v)] = score
		total_score += score
	scores[1] = int(completed_games/2 - total_score + 0.5)
	if completed_games_this_week == 0:
		del(scores[num_weeks])
	return scores

def standings(week_number,yes_monkey=True):
	matrix = score_matrix(yes_monkey)
	best_score = 0
	for k,v in matrix.items():
		if week_number in matrix[k]:
			matrix[k] = matrix[k][week_number]
			if matrix[k] >= best_score:
				best_score = matrix[k]
				if k != 'Monkey':
					matrix[k] += Monday.objects.get(week_number=week_number,player=User.objects.get(username=k)).bonus()
		else:
			matrix[k] = 0

	if yes_monkey == True:
		matrix['Monkey'] += 0.01
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
				if player == 'Monkey':
					continue
				user = User.objects.get(username=player)
				bonus = Monday.objects.get(player=user, week_number=week_number).bonus()
				if bonus > best_bonus:
					leader = player
					best_bonus = bonus
			return leader

def overall_total(sm = None):
	if sm is None:
		sm = score_matrix()
	total = {}
	for player, scores in sm.items():
		total[player] = sum(scores.values())
	if 'Monkey' in total.keys():
		total['Monkey'] = total['Monkey'] + 0.01
	rank_order = sorted(total.items(), key=lambda kv: kv[1], reverse=True)
	if 'Monkey' in total.keys():
		idx = rank_order.index(('Monkey',total['Monkey']))
		total['Monkey'] = int(total['Monkey'])
		rank_order[idx] = ('Monkey',int(total['Monkey']))
	return (total, rank_order)

def overall(sm = None):
	if sm is None:
		sm = score_matrix()
	if sm == {}:
		return []

	(total,rank_order) = overall_total(sm)
	winner = {}
	for week in list(sm[rank_order[0][0]].keys()):
		winner[week] = whoWon(week,sm)

	table = []
	for item in rank_order:
		player = item[0]
		this_row = [[player,0]]
		weeks = list(sm[player].keys())
		weeks.sort()
		for week in weeks:
			win = 0
			if winner[week] == player:
				win=1
			this_row.append([sm[player][week],win])
		this_row.append([total[player],0])
		table.append(this_row)
	return table
