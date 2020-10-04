# -*- coding: future_fstrings -*-
from pool.models import Team,Game,Pick,Bank,Blog,Monday,now,Main
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import requests
import json
import csv
from datetime import datetime, timedelta, timezone
import random
from django.core import serializers
from os import mkdir,path as path_

def choose_art():
	default_image = 'http://www.tammer.com/home_page_chimp.jpeg'
	response = requests.get('http://www.tammer.com/poolart/art.csv')
	if response.status_code != 200:
		return default_image
	else:
		eligible = []
		wrapper = list(csv.reader(response.text.strip().split('\n')))
		for this_row in wrapper:
			if len(this_row) != 2:
				continue
			if int(this_row[1] ) == 1:
				eligible.append(this_row[0])
		if not(eligible):
			return default_image
		else:
			idx = int(now().minute / 60 * len(eligible))
			return eligible[idx]

def deposit(who, amount, note):
	if who == 'all':
		if amount is None:
			for user in User.objects.all():
				amount = input(user.username+': ')
				y = Bank()
				y.player = user
				y.deposit_amount = amount
				y.note = note
				y.save()
		else:
			for user in User.objects.all():
				y = Bank()
				y.player = user
				y.deposit_amount = amount
				y.note = note
				y.save()
			return "OK"
	else:
		if amount is None:
			return 'NOT OK. Doing nothing because amount is None'
		else:
			user = User.objects.get(username=who)
			y = Bank()
			y.player = user
			y.deposit_amount = amount
			y.note = note
			y.save()
			return "OK"


# assumes table is empty. if it is not, you need to delete() it first
def restore(filename):
	f = open(filename, "r")
	data = f.read()
	for obj in serializers.deserialize("json", data):
		obj.save()

def rebuild(path):
	tables = ['User','Team','Game','Pick','Bank','Monday']
	for table in tables:
		print(table)
		globals()[table].objects.all().delete()
		restore(path+'/'+table+".json")


def backup():
		tables = ['Team','Game','Pick','Bank','Monday','User']
		dir_name = datetime.now().strftime('%d')
		path = 'backups/'+dir_name
		if not(path_.exists(path)):
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
		if game.game_date.timetuple().tm_yday == now().timetuple().tm_yday:
			if game.game_date < now():
				g['game_day'] = 'now'
			else:
				g['game_day'] = game.game_date.strftime('%-I:%M')
		else:
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
# use any text for the team name as long as team_from_string can parse it
def set_score(week_number, score):
	try:
		udog = team_from_string( list(score.keys())[0] )
		udog_score = score[list(score.keys())[0]]
		fav = team_from_string( list(score.keys())[1] )
		fav_score = score[list(score.keys())[1]]
	except:
		msg = f'Cannot find a team matching on of (or both) {list(score.keys())[0]} or {list(score.keys())[1]}'
		raise( NameError(msg) )
	try:
		game = Game.objects.get(week_number=week_number,fav=fav, udog=udog)
	except:
		temp = udog
		udog = fav
		fav = temp
		temp = udog_score
		udog_score = fav_score
		fav_score = temp
	try:
		game = Game.objects.get(week_number=week_number,fav=fav, udog=udog)
	except:
		msg = f'{fav.short_name} is not playing {udog.short_name} in week {week_number}'
		raise( NameError(msg) )
	game.fav_score = fav_score
	game.udog_score = udog_score
	game.save()
	print('---')
	print(game.as_string())
	print('---')
	return game

def load_teams():
	Team.objects.all().delete()
	url = 'http://www.tammer.com/teams.csv'
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

def load_scores():
	week_number = implied_week()
	url = 'https://api-secure.sports.yahoo.com/v1/editorial/s/scoreboard?leagues=nfl&week='+str(week_number)
	# url = 'http://www.tammer.com/test_data.json'
	response = requests.get(url)
	if response.status_code != 200:
		print('Failed to get data:', response.status_code)
	else:
		root = json.loads(response.text)
		for k,v in root['service']['scoreboard']['games'].items():
			if 'final' in v['status_type']:
				h = root['service']['scoreboard']['teams'][v['home_team_id']]['last_name']
				a = root['service']['scoreboard']['teams'][v['away_team_id']]['last_name']
				asc = int(v['total_away_points'])
				hsc = int(v['total_home_points'])
				ht = team_from_string(h)
				at = team_from_string(a)
				set_score(week_number,{ht.nick_name:hsc, at.nick_name:asc})




def load_games(this_year):
	Game.objects.all().delete()
	for x in range(17):
		week_number = x+1
		url = 'https://api-secure.sports.yahoo.com/v1/editorial/s/scoreboard?leagues=nfl&week='+str(week_number)+'&season='+str(this_year)
		response = requests.get(url)
		if response.status_code != 200:
			print('Failed to get data:', response.status_code)
		else:
			i=0
			root = json.loads(response.text)
			# create dictionary that is sortable by game date
			# the j thing makes sures games with exact same start time have different keys	
			new_dict = {}
			j=0.001
			for k,v in root['service']['scoreboard']['games'].items():
				new_key	= datetime.strptime(v['start_time'],'%a, %d %b %Y %H:%M:%S %z').timestamp()
				new_key = new_key + j
				j = j + 0.001
				new_dict[new_key] = v

			for k,v in sorted(new_dict.items()):
				h = root['service']['scoreboard']['teams'][v['home_team_id']]['last_name']
				a = root['service']['scoreboard']['teams'][v['away_team_id']]['last_name']
				gm_dt = datetime.strptime(v['start_time'],'%a, %d %b %Y %H:%M:%S %z')
				gm_dt = gm_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
				gm_dt = gm_dt.replace(tzinfo=None)
				print(a +" at "+h+"\t\t"+gm_dt.strftime('%A %d-%b-%Y %H:%M:%S'))
				
				
				Game.objects.create(
					week_number = week_number, game_number=i+1,
					fav = team_from_string(h),
					udog = team_from_string(a),
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
	init_user(user)

def init_user(user):
	Pick.objects.filter(player=user).delete()
	for game in Game.objects.all():
		pick = Pick(week_number=game.week_number, game_number=game.game_number, player=user,picked_fav=True)
		pick.save(force=True)
	Monday.objects.filter(player=user).delete()
	for game in Game.objects.filter(game_number=1):
		monday = Monday(week_number=game.week_number,player=user,total_points=0)
		monday.save(force=True)

def init_all_users():
	for user in User.objects.all():
		init_user(user)

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
	random.seed(1)
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

	if yes_monkey == True and matrix != {}:
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

def team_from_string(string):
	string = string.replace("New York","NY")
	string = string.replace("Los Angeles","LA")
	string = string.replace("Football Team","Football-Team")
	for team in Team.objects.all():
		if string.lower() in team.short_name.lower():
			return team
	for team in Team.objects.all():
		if string.lower() in team.full_name.lower():
			return team
	raise(NameError(f'{string} could not be recognized as any team'))

def grab_game(week_number,team_string):
	team = team_from_string(team_string)
	try:
		return Game.objects.get(week_number=week_number,udog=team)
	except:
		return Game.objects.get(week_number=week_number,fav=team)

def load_spreads(week_number):
	url = f'https://fantasydata.com/NFL_Odds/Odds_Read?season=2020&week={week_number}&seasontype=1&oddstate=NJ&teamkey=ARI&subscope=2&scope=1'
	response = requests.get(url)
	if response.status_code != 200:
		print('Failed to get data:', response.status_code)
	else:
		i=0
		root = json.loads(response.text)
		raw = root['Raw']
		root2 = json.loads(raw)
		for node in root2:
			for k in ['HomeTeam','AwayTeam','PointSpread']:
				print(node[k])
			g = grab_game(week_number,node['HomeTeam'])
			spread = float(node['PointSpread'])
			if spread < 0:
				g.setFav(team_from_string(node['HomeTeam']),-int(spread))
			else:
				g.setFav(team_from_string(node['AwayTeam']),int(spread))
			print(g.as_string())
			g.save()
			print('')

def delete_game(week_number, game_number):
	Game.objects.get(week_number=week_number,game_number=game_number).delete()
	Pick.objects.filter(week_number=week_number,game_number=game_number).delete()


def stats():
	result = {}
	result['fav_wins'] = 0
	result['udog_wins'] = 0
	result['home_wins'] = 0
	result['away_wins'] = 0
	result['homedog_wins'] = 0
	result['awaydog_wins'] = 0
	result['homefav_wins'] = 0
	result['awayfav_wins'] = 0
	for g in Game.objects.exclude(fav_score__isnull=True):
		if g.favWins():
			result['fav_wins'] += 1
			if g.fav_is_home:
				result['home_wins'] += 1
				result['homefav_wins'] += 1
			else:
				result['away_wins'] += 1
				result['awayfav_wins'] += 1
		else:
			result['udog_wins'] += 1
			if g.fav_is_home:
				result['away_wins'] += 1
				result['awaydog_wins'] += 1
			else:
				result['home_wins'] += 1
				result['homedog_wins'] += 1
	return result
