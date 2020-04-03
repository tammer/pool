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
import pool.utils
from pool.utils import score_matrix as scoreMatrix, standings as standings_,implied_week,status as status_

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

def overall(request):
	week_number = implied_week()
	table = pool.utils.overall()
	headers = []
	if table != []:
		headers = range(1,len(table[0])-1)
	return render(request, 'pool/overall.html',{'week_number':week_number, 'table':table, 'headers':headers})

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
		if game.spread == 0:
			spread = ''
		else:
			spread = str(game.spread)
		header.append([game.favShortName(), spread+"&frac12;", game.udogShortName(), game.game_date.strftime('%a')])
	header.append('MNTP')
	matrix = {}
	for user in User.objects.all().order_by('username'):
		matrix[user.username] = [];
		monday_ok_to_show = True
		for pick in Pick.objects.filter(player=user,week_number=week_number).order_by('game_number'):
			if Game.objects.get(week_number=week_number,game_number=pick.game_number).isClosed():
				matrix[user.username].append(pick.whoShortName())
			else:
				monday_ok_to_show = False
				matrix[user.username].append('')
		try:
			tp = Monday.objects.get(week_number=week_number,player=user).total_points
			if tp is None or not(monday_ok_to_show):
				tp = ''
		except:
			tp = ''
		matrix[user.username].append( tp )
	return render(request, 'pool/allpicks.html', {'week_number': week_number, 'header': header, 'matrix': matrix})

def results(request):
	if request.GET.get('w'):
		week_number = int(request.GET['w'])
	else:
		week_number = implied_week()

	latest_week = False
	if week_number == implied_week():
		latest_week = True
	if now().date() < Game.objects.get(week_number=week_number,game_number=1).game_date.date() and week_number > 2:
		week_number -= 1;

	show_results = True
	if request.GET.get('p'):
		player = request.GET['p']
	else:
		if request.user.is_authenticated:
			player = request.user.username
		else:
			show_results = False;
			player = User.objects.all().first() # just a place holder; we wont show anyones results
	games = []
	user = User.objects.get(username=player)
	right = 0
	right_array = []
	total = 0
	completed = 0;
	for game in Game.objects.filter(week_number=week_number).order_by('game_number'):
		total+=1
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
		if g['spread'] == 0:
			g['spread'] = ''
		pick = Pick.objects.get(player=user, week_number=week_number, game_number = game.game_number)
		if pick.isCorrect():
			g['right'] = "Yes"
			right += 1
			right_array.append('a banana!')
		else:
			g['right'] = "No"
		if pick.game().isOver():
			completed += 1
		g['picked_fav'] = pick.picked_fav
		g['isOver'] = game.isOver()
		g['game_day'] = game.game_date.strftime('%A')
		games.append(g)
	return render(request, 'pool/results.html',{ 'latest_week':latest_week, 'completed':completed, 'right_array':right_array,  'week_number': week_number, 'standings':standings_(week_number=week_number), 'games': games, 'player': player, 'right': right, 'total': total, 'show_results':show_results } )

def home(request):

	(headline_week_number,status) = status_()
	week_number = headline_week_number
	if status == "Not Open" and headline_week_number > 1:
		week_number = headline_week_number-1
	
	# Standings
	standings = standings_(week_number)
	sm = scoreMatrix()
	total = {}
	for p, scores in sm.items():
		total[p] = sum(scores.values())
	rank_order = sorted(total.items(), key=lambda kv: kv[1], reverse=True)

	# Blog
	blog_list = []
	for blog in Blog.objects.all().order_by('-entry_date')[:4]:
		blog_list.append([blog.entry_date.strftime('%A %B %-d'), blog.entry])
	first_blog_date = blog_list[0][0]
	first_blog = blog_list[0][1]
	id = Blog.objects.all().order_by('-entry_date').first().id
	blog_list.pop(0)

	completed = Game.objects.filter(week_number=week_number,fav_score__isnull = False).count()
	total = Game.objects.filter(week_number=week_number).count()

	pics = [
		'https://i.ytimg.com/vi/0-K9kUQ1_PE/maxresdefault.jpg',
		'http://www.tammer.com/Chimp-352-570x270.jpg',
		'https://technologytherapy.com/wp-content/uploads/2018/06/getmonkeys-2-768x384.jpg',
		'https://i.pinimg.com/originals/4d/79/c8/4d79c81a255ac387c4cdaea7c1e5ac4d.jpg',
		'https://www.wakingtimes.com/wp-content/uploads/2017/10/thinking-monkey-1.jpg',
		'https://i.ytimg.com/vi/6WRLFiujDFY/maxresdefault.jpg',
	]
	index = now().hour % len(pics)
	src = pics[index]

	time = now().strftime('%A %B %-d %-I:%M %p')

	ng_text = ''
	if now() < Game.objects.all().order_by('game_date').last().game_date:
		ng = Game.objects.filter(game_date__gt = now()).order_by('game_date').first()
		game_day = ng.game_date.strftime("%A")
		if game_day == now().strftime("%A"):
			game_day = 'Today'
		ng_text = f'Next Game: {game_day} at {ng.game_date.strftime("%-I:%M%p").lower().replace("pm","p")} ({ng.awayNickName()} @ {ng.homeNickName()})'

	if status == "Open":
		message1 = '<font color="#33A532">OPEN</font> until Sunday 1:00 PM'
		message2 = ng_text
	elif status == "Not Open":
		message1 = '<font color="#FFBF00">Not Open Yet.</font>'
		message2 = ng_text
	else:
		message1 = '<font color="red">Closed</font>'
		message2 = f'{completed} of {total} games completed'

	return render(request, 'pool/home.html',{'headline_week_number':headline_week_number, 'time':time, 'message1':message1,'message2':message2, 'status':status, 'src':src, 'total':total, 'completed':completed, 'id':id, 'rest_of_blog':blog_list, 'first_blog_date':first_blog_date, 'first_blog':first_blog, 'player':request.user.username, 'standings':standings, 'overall': rank_order, 'week_number': week_number})

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
	if request.user.is_authenticated:
		user = request.user
	else:
		return redirect('login')	

	(week_number,status) = status_()
	if status == 'Closed':
		messages.warning(request,f'Week {week_number} is closed.')
		return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
	if status == 'Not Open':
		messages.warning(request,f'Sorry, week {week_number} is not open for picks yet.')
		return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


	queryset = Pick.objects.filter(week_number=week_number,player=user).order_by('game_number').all()
	formset = PickFormSet(queryset=queryset)
	(monday_instance, created) = Monday.objects.get_or_create(player=user, week_number=week_number)
	if monday_instance.total_points == 0:
		monday_instance.total_points = None # will cause the form to force the dude to put something in
	monday_form = MondayForm(instance=monday_instance)
	disabled = ''
	
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



