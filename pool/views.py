from django.shortcuts import render
from django.http import HttpResponse
from pool.models import Team,Game,Pick,Bank
from django.contrib.auth.models import User
from django.db.models import Sum

def money(request):
	table = {}
	for user in User.objects.all():
		value = Bank.objects.filter(player=user).aggregate(Sum('deposit_amount'))['deposit_amount__sum']
		table[user.username] = value
		# table[user.username] = "{:.2f}".format(value)
	table = sorted(table.items(), key=lambda kv: kv[1], reverse=True)
	table2 = []
	for row in table:
		table2.append([row[0],"{:.2f}".format(row[1])])

	table3 = []
	for row in Bank.objects.filter(player=request.user).order_by('-transaction_date'):
		table3.append([
			row.transaction_date.strftime("%b %-d, %Y"),
			"{:.2f}".format(row.deposit_amount),
			row.note])

	return render(request, 'pool/money.html',{'player':request.user.username, 'table':table2, 'table2':table3})

def whoWon(week_number, score_matrix):
	#!!! still have to add MNTP logic
	leader = None
	best_score = 0
	for player, score in score_matrix.items():
		if score[week_number] > best_score:
			best_score = score[week_number]
			leader = player
	if best_score == 0:
		return None
	else:
		return leader

def scoreMatrix():
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

def overall(request):
	week_number = request.GET['w']
	sm = scoreMatrix()
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
	headers = range(1,len(table[0])-1)
	return render(request, 'pool/overall.html',{'week_number':week_number, 'table':table, 'headers':headers})



def standings_(week_number):
	matrix = {}
	for user in User.objects.all():
		count = 0;
		for pick in Pick.objects.filter(player=user,week_number=week_number):
			if pick.isCorrect():
				count +=1
		matrix[user.username] = count
		standings = sorted(matrix.items(), key=lambda kv: kv[1], reverse=True)
	return standings

def standings(request):
	if request.GET.get('p'):
		player = request.GET['p']
	else:
		player = ''
	return render(request,'pool/standings.html',{'player':player,'week_number':request.GET['w'],'standings':standings_(request.GET['w'])})

def allpicks(request):
	week_number = request.GET['w']
	header = []
	for game in Game.objects.filter(week_number=week_number).order_by('game_number'):
		header.append([game.favShortName(), str(game.spread), game.udogShortName(), game.game_date.strftime('%a')])
	matrix = {}
	for user in User.objects.all().order_by('username'):
		matrix[user.username] = [];
		for pick in Pick.objects.filter(player=user,week_number=week_number).order_by('game_number'):
			matrix[user.username].append(pick.whoShortName())
	return render(request, 'pool/allpicks.html', {'week_number': week_number, 'header': header, 'matrix': matrix})

def results(request):
	week_number = request.GET['w']
	if request.GET.get('p'):
		player = request.GET['p']
	else:
		player = request.user.username
	games = []
	user = User.objects.get(username=player)
	right = 0
	right_array = []
	total = 0
	completed = 0;
	for game in Game.objects.filter(week_number=week_number).order_by('game_number'):
		g = {}
		# !!! change to function shortName()
		if game.fav_is_home:
			g['fav'] = game.fav.nick_name.upper()
			g['udog'] = game.udog.nick_name.lower()
		else:
			g['fav'] = game.fav.nick_name.lower()
			g['udog'] = game.udog.nick_name.upper()
		g['fav_score'] = game.fav_score
		g['udog_score'] = game.udog_score
		if game.spread is None:
			g['spread'] = 'NA'
		else:
			g['spread'] = round(game.spread - 0.1) # we'll display 1/2 nicely
		pick = Pick.objects.get(player=user, week_number=week_number, game_number = game.game_number)
		if pick.isCorrect():
			g['right'] = "Yes"
			right += 1
			right_array.append('a banana!')
		else:
			g['right'] = "No"
		if pick.game().isOver():
			completed += 1
		total+=1
		g['picked_fav'] = pick.picked_fav
		g['isOver'] = game.isOver()
		g['game_day'] = game.game_date.strftime('%A')
		games.append(g)
	return render(request, 'pool/results.html',{'completed':completed, 'right_array':right_array,  'week_number': week_number, 'standings':standings_(week_number=week_number), 'games': games, 'player': player, 'right': right, 'total': total} )

def home(request):
	return HttpResponse("<h1>Hello World</h1>")

def teams(request):
	teams = Team.objects.all()
	return render(request, 'pool/teams.html', {'teams': teams} )

def games(request):
	week_number = request.GET['w']
	current_date = ''
	games = {}
	for game in Game.objects.filter(week_number=week_number).order_by('game_number'):
		dt = game.game_date.strftime('%A, %B %-d')
		if dt != current_date:
			games[dt] = []
			current_date = dt
		g={}
		if game.fav_is_home:
			g['fav'] = game.fav.full_name.upper()
			g['udog'] = game.udog.full_name.lower()
		else:
			g['fav'] = game.fav.full_name.lower()
			g['udog'] = game.udog.full_name.upper()
		g['time'] = game.game_date.strftime('%-I:%M%p').lower().replace('pm','p')
		if game.spread is None:
			g['spread'] = 'NA'
		else:
			g['spread'] = game.spread
		games[dt].append(g)
	return render(request, 'pool/games.html', {'games': games} )