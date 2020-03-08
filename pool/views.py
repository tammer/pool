from django.shortcuts import render
from django.http import HttpResponse
from pool.models import Team,Game,Pick
from django.contrib.auth.models import User


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
	player_name = request.GET['p']
	games = []
	user = User.objects.get(username=player_name)
	right = 0
	total = 0
	for game in Game.objects.filter(week_number=week_number).order_by('game_number'):
		g = {}
		# !!! change to function shortName()
		if game.fav_is_home:
			g['fav'] = game.fav.full_name.upper()
			g['udog'] = game.udog.full_name.lower()
		else:
			g['fav'] = game.fav.full_name.lower()
			g['udog'] = game.udog.full_name.upper()
		g['fav_score'] = game.fav_score
		g['udog_score'] = game.udog_score
		if game.spread is None:
			g['spread'] = 'NA'
		else:
			g['spread'] = game.spread
		pick = Pick.objects.get(player=user, week_number=week_number, game_number = game.game_number)
		if pick.isCorrect():
			g['right'] = "Yes"
			right += 1
		else:
			g['right'] = "No"
		total+=1
		g['picked_fav'] = pick.picked_fav
		games.append(g)
	return render(request, 'pool/results.html', {'games': games, 'player': player_name, 'right': right, 'total': total} )




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