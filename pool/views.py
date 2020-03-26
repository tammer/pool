from django.shortcuts import render, redirect
from django.http import HttpResponse
from pool.models import Team,Game,Pick,Bank,Blog
from django.contrib.auth.models import User
from django.db.models import Sum
from .forms import BankForm,BlogForm,PickForm
from django.contrib import messages
from django.urls import reverse
import random,datetime
from django.forms import modelformset_factory


def impliedWeek():
	first_week_without_a_score = Game.objects.filter(fav_score__isnull = True).order_by('week_number').first().week_number
	if Game.objects.filter(week_number = first_week_without_a_score, fav_score__isnull = False).order_by('week_number').first().week_number == first_week_without_a_score:
		# first_week_without_a_score has nuls and scores.  This must be the week we're in
		return first_week_without_a_score
	else:
		return first_week_without_a_score + 1

def deposit(request):
	form = BankForm(request.POST)
	if request.user.is_superuser and form.is_valid():
		player = form.cleaned_data.get('player')
		form.save()
		messages.success(request, f'Account balance has been updated for {player}')
		url = reverse('pool-money')+f'?p={player}'
		return redirect(url,{'p':player})
	else:
		messages.warning(request, f'Not!')
		return redirect('pool-money')

def money(request):
	table = {}
	for user in User.objects.all():
		value = Bank.objects.filter(player=user).aggregate(Sum('deposit_amount'))['deposit_amount__sum']
		table[user.username] = value
		# table[user.username] = "{:.2f}".format(value)
	table = sorted(table.items(), key=lambda kv: kv[1], reverse=True)
	table2 = []
	for row in table:
		table2.append([row[0],"{:.0f}".format(row[1])])

	table3 = []
	player = request.user
	if request.user.is_superuser:
		if request.GET.get('p'):
			player = User.objects.get(username=request.GET['p'])

	for row in Bank.objects.filter(player=player).order_by('-transaction_date'):
		table3.append([
			row.transaction_date.strftime("%b %-d, %Y"),
			"{:.0f}".format(row.deposit_amount),
			row.note])

	return render(request, 'pool/money.html',{'is_superuser':request.user.is_superuser, 'form':BankForm(),  'player':player.username, 'table':table2, 'table2':table3})

def blog(request):
	if request.GET.get('id'):
		id = request.GET['id']
		blog = Blog.objects.get(id=id)
		form = BlogForm(instance=blog)
	else:
		form = BlogForm()
		id = ''
	return render(request, 'pool/blog.html',{'form':form, 'id':id})

def post(request):
	if request.GET.get('id'):
		id = request.GET['id']
		blog = Blog.objects.get(id=id)
		form = BlogForm(request.POST, instance=blog)
	else:
		form = BlogForm(request.POST)
	if request.user.is_superuser and form.is_valid():
		form.save()
		messages.success(request, f'Update Completed')
		return redirect('pool-home')
	else:
		messages.warning(request, f'You are not logged in as someone who is authorized to do this action.  Try logging in as Adel')
		return redirect('pool-blog')


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
	week_number = impliedWeek()
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
	if request.GET.get('p'):
		week_number = request.GET['w']
	else:
		week_number = impliedWeek()
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
	if request.GET.get('p'):
		week_number = request.GET['w']
	else:
		week_number = impliedWeek()

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
	if request.GET.get('p'):
		week_number = request.GET['w']
	else:
		week_number = impliedWeek()
	player = request.user.username
	standings = standings_(week_number)
	sm = scoreMatrix()
	total = {}
	for p, scores in sm.items():
		total[p] = sum(scores.values())
	rank_order = sorted(total.items(), key=lambda kv: kv[1], reverse=True)
	ng = Game.objects.filter(fav_score__isnull = True).order_by('game_date').first()
	next_game = f'{ng.awayNickName()} @ {ng.homeNickName()} {ng.game_date.strftime("%A")} at {ng.game_date.strftime("%-I:%M%p").lower().replace("pm","p")}'

	blog_list = []
	for blog in Blog.objects.all().order_by('-entry_date')[:4]:
		blog_list.append([blog.entry_date.strftime('%A %B %-d'), blog.entry])
	first_blog_date = blog_list[0][0]
	first_blog = blog_list[0][1]
	id = Blog.objects.all().order_by('-entry_date').first().id
	blog_list.pop(0)
	completed = Game.objects.filter(week_number=week_number,fav_score__isnull = False).count()
	total = Game.objects.filter(week_number=week_number).count()
	random.seed(week_number+datetime.datetime.now().day)
	src = random.choice([
		'http://www.tammer.com/Chimp-352-570x270.jpg',
		'https://technologytherapy.com/wp-content/uploads/2018/06/getmonkeys-2-768x384.jpg',
		'https://i.pinimg.com/originals/4d/79/c8/4d79c81a255ac387c4cdaea7c1e5ac4d.jpg',
		'https://www.wakingtimes.com/wp-content/uploads/2017/10/thinking-monkey-1.jpg',
		'https://i.ytimg.com/vi/6WRLFiujDFY/maxresdefault.jpg',
		])
	return render(request, 'pool/home.html',{'src':src, 'total':total, 'completed':completed, 'id':id, 'is_superuser':request.user.is_superuser, 'rest_of_blog':blog_list, 'first_blog_date':first_blog_date, 'first_blog':first_blog, 'next_game':next_game, 'player':player, 'standings':standings, 'overall': rank_order, 'week_number': week_number})

def teams(request):
	teams = Team.objects.all()
	return render(request, 'pool/teams.html', {'teams': teams} )

PickFormSet = modelformset_factory(Pick,extra=0, form = PickForm, fields=('game_number','week_number','picked_fav' ))
def dopicks(request):
	user = request.user	
	queryset = Pick.objects.filter(week_number=7,player=user).order_by('game_number').all()
	formset = PickFormSet(queryset=queryset)
	return render(request, 'pool/dopicks.html', {'formset':formset} )	

def postpicks(request):
	formset = PickFormSet(request.POST)
	if formset.is_valid():
		instances = formset.save()
		messages.success(request, "Picks Updated")
	else:
		print("Trouble at the Mill")
		messages.warning(request, formset.errors	)
	return redirect('pool-dopicks')

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



