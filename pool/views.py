from django.shortcuts import render, redirect
from django.http import HttpResponse
from pool.models import Team,Game,Pick,Bank,Blog,Monday,now
from django.contrib.auth.models import User
from django.db.models import Sum
from .forms import BankForm,BlogForm,PickForm,MondayForm,SpreadForm
from django.contrib import messages
from django.urls import reverse
import random
from datetime import datetime, timedelta
from django.forms import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect



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

def dead_list(start=1, end=None):
	week_number = end
	if week_number is None:
		week_number = implied_week()
	score_matrix = scoreMatrix()
	results = set()
	while week_number > start-1:
		min_score = 99;
		for player, score in score_matrix.items():
			if score[week_number] < min_score:
				min_score = score[week_number]
		for player, score in score_matrix.items():
			if score[week_number] == min_score:
				results.add(player)
		week_number -= 1;
	return results

def overall(request):
	week_number = implied_week()
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
	standings2 = []
	dl = dead_list(1,week_number-1)
	for item in standings:
		dead = False
		if item[0] in dl:
			dead = True
		standings2.append([item[0],item[1],dead])
	return standings2

def standings(request):
	if request.GET.get('p'):
		player = request.GET['p']
	else:
		player = ''
	return render(request,'pool/standings.html',{'player':player,'week_number':int(request.GET['w']),'standings':standings_(int(request.GET['w']))})

def allpicks(request):
	if request.GET.get('w'):
		week_number = int(request.GET['w'])
	else:
		week_number = implied_week()
	header = []
	for game in Game.objects.filter(week_number=week_number).order_by('game_number'):
		header.append([game.favShortName(), str(game.spread)+"&frac12;", game.udogShortName(), game.game_date.strftime('%a')])
	header.append('MNTP')
	matrix = {}
	for user in User.objects.all().order_by('username'):
		matrix[user.username] = [];
		for pick in Pick.objects.filter(player=user,week_number=week_number).order_by('game_number'):
			if Game.objects.get(week_number=week_number,game_number=pick.game_number).isClosed():
				matrix[user.username].append(pick.whoShortName())
			else:
				matrix[user.username].append('')
		try:
			tp = Monday.objects.get(week_number=week_number,player=user).total_points
			if tp is None:
				tp = ''
		except:
			tp = ''
		matrix[user.username].append( tp )
	return render(request, 'pool/allpicks.html', {'week_number': week_number, 'header': header, 'matrix': matrix})

def results(request):
	if request.GET.get('p'):
		week_number = int(request.GET['w'])
	else:
		week_number = implied_week()

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
		if game.isOpen():
			continue
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
			g['spread'] = game.spread
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
	if request.GET.get('w'):
		week_number = int(request.GET['w'])
	else:
		week_number = implied_week()
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
	random.seed(week_number+now().day)
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

def spreads(request):
	if not(request.user.is_superuser):
		messages.warning(request, "Unauthorized")
		return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
	SpreadFormSet = modelformset_factory(Game,extra=0, form = SpreadForm, fields=('spread',))
	if request.GET.get('w'):
			week_number = int(request.GET['w'])
	else:
			week_number = implied_week(delta_hours=0)

	if request.method == "POST":
		formset = SpreadFormSet(request.POST)
		if formset.is_valid():
			formset.save()
			messages.success(request,"Spreads Updated Successfully")
		else:
			print("Trouble at the Mill")
			messages.warning(request, formset.errors)
	queryset = Game.objects.filter(week_number=week_number).order_by('game_number').all()
	formset = SpreadFormSet(queryset=queryset)
	return render(request, 'pool/spreads.html', { 'week_number':week_number, 'formset':formset})

PickFormSet = modelformset_factory(Pick,extra=0, form = PickForm, fields=('game_number','week_number','picked_fav' ))
def dopicks(request):
	user = request.user
	week_number = implied_week()
	queryset = Pick.objects.filter(week_number=week_number,player=user).order_by('game_number').all()
	formset = PickFormSet(queryset=queryset)
	(monday_instance, created) = Monday.objects.get_or_create(player=user, week_number=week_number)
	monday_form = MondayForm(instance=monday_instance)
	disabled = ''
	if Game.objects.filter(week_number=week_number).order_by('game_number').last().isClosed():
		messages.warning(request,f'Week {week_number} is closed.')
		return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
	now_ = now().strftime('%A %B %-d %-I:%M %p')
	return render(request, 'pool/dopicks.html', { 'now':now_, 'disabled':disabled, 'player':user.username, 'week_number':week_number, 'formset':formset, 'monday_form':monday_form} )

def postpicks(request):
	user = request.user
	week_number = implied_week()
	formset = PickFormSet(request.POST)
	monday_instance = Monday.objects.get(player=user, week_number=week_number)
	monday_form = MondayForm(request.POST, instance = monday_instance)
	if formset.is_valid() and monday_form.is_valid():
		instances = formset.save()
		monday_form.save()

		team=''
		game_number = random.choice([4,5,6,7,8,9])
		if instances[game_number].picked_fav:
			team = Game.objects.get(week_number=week_number,game_number=instances[game_number].game_number).fav.city_name
		else:
			team = Game.objects.get(week_number=week_number,game_number=instances[game_number].game_number).udog.city_name
		message = random.choice(['Picks Updated. (You should probably reverse.)',f'Picks Updated. (You took {team}?? Not smart.)'])
		if random.random() < 0.63:
			message = 'Picks Updated.'
		messages.success(request, message)
	else:
		print("Trouble at the Mill")
		messages.warning(request, formset.errors + monday_form.errors	)
	return redirect('pool-dopicks')

def games(request):
	week_number = int(request.GET['w'])
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



