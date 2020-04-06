# -*- coding: future_fstrings -*-
from django.db import models
from django.contrib.auth.models import User
import datetime
from pytz import timezone

def now():
	text_file = open("now.txt", "r")
	string_list = text_file.read().split(',')
	list = []
	for string in string_list:
		list.append(int(string))
	return datetime.datetime(*list)

class Team(models.Model):
	full_name = models.CharField(max_length=50)
	short_name = models.CharField(max_length=3)
	nick_name = models.CharField(max_length=50)
	city_name = models.CharField(max_length=50)

class Game(models.Model):
	week_number = models.IntegerField()
	game_number = models.IntegerField()
	fav =  models.ForeignKey(Team, related_name='fav_games', on_delete=models.CASCADE)
	udog = models.ForeignKey(Team, related_name='udog_games', on_delete=models.CASCADE)
	spread = models.IntegerField( null=True )
	game_date = models.DateTimeField()
	fav_score = models.IntegerField( null=True )
	udog_score = models.IntegerField( null=True )
	fav_is_home = models.BooleanField()
	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['week_number', 'game_number'], name='unique_week_game'),
			#spread >=0
		]
	
	def totalPoints(self):
		if self.fav_score is None or self.udog_score is None:
			return None
		else:
			return self.fav_score+self.udog_score

	def save(self, *args, **kwargs):
		if not(self.spread is None) and self.spread < 0:
			self.spread = -self.spread
			temp = self.fav
			self.fav = self.udog
			self.udog = temp
			self.fav_is_home = not(self.fav_is_home)
		super(Game, self).save(*args, **kwargs)

	def favFullName(self):
		if self.fav_is_home:
			return self.fav.full_name.upper()
		else:
			return self.fav.full_name.lower()

	def udogFullName(self):
		if not(self.fav_is_home):
			return self.udog.full_name.upper()
		else:
			return self.udog.full_name.lower()

	def favShortName(self):
		if self.fav_is_home:
			return self.fav.short_name.upper()
		else:
			return self.fav.short_name.lower()

	def udogShortName(self):
		if not(self.fav_is_home):
			return self.udog.short_name.upper()
		else:
			return self.udog.short_name.lower()

	def favNickName(self):
		if self.fav_is_home:
			return self.fav.nick_name.upper()
		else:
			return self.fav.nick_name.lower()

	def udogNickName(self):
		if not(self.fav_is_home):
			return self.udog.nick_name.upper()
		else:
			return self.udog.nick_name.lower()


	def homeNickName(self):
		if self.fav_is_home:
			return self.fav.nick_name
		else:
			return self.udog.nick_name

	def awayNickName(self):
		if self.fav_is_home:
			return self.udog.nick_name
		else:
			return self.fav.nick_name


	def isClosed(self, current_time = None):
		if current_time is None:
			current_time = now()
		if self.game_date.weekday() == 0: # Monday
			distance_to_sunday = -1
		else:
			distance_to_sunday = 6 - self.game_date.weekday()
		current_sunday = self.game_date + datetime.timedelta(distance_to_sunday)
		current_sunday = current_sunday.replace(hour=13, minute=0, second=0)
		if current_time > current_sunday or current_time > self.game_date:
			return True
		else:
			return False

	def isOver(self):
		if self.fav_score is None or self.udog_score is None:
			return False
		else:
			return True

	def isOpen(self, current_time = None):
		return not(self.isClosed(current_time = current_time))


	def favWins(self):
		# throw exception if scores are not filled in
		if self.fav_score - self.udog_score > self.spread:
			return True
		else:
			return False

class Pick(models.Model):
	player = models.ForeignKey(User,on_delete=models.CASCADE)
	week_number = models.IntegerField()
	game_number = models.IntegerField()
	picked_fav = models.BooleanField()

	def save(self, *args, **kwargs):
		force = False
		try:
			force = kwargs.pop('force')
		except:
			pass
		if not(force) and Game.objects.get(game_number=self.game_number,week_number=self.week_number).isClosed():
			# You can't change this pick!
			err = f'Not actually saving. You are trying to change a pick for a game that isClosed. week: {self.week_number} game:{self.game_number}. If you want to do this use force=True' 
			print(err)
		else:
			super(Pick, self).save(*args, **kwargs)

	def game(self):
		return Game.objects.get(week_number=self.week_number, game_number=self.game_number)

	def whoShortName(self):
		if self.picked_fav:
			return self.game().favShortName()
		else:
			return self.game().udogShortName()

	def isCorrect(self):
		game = Game.objects.get(week_number=self.week_number, game_number=self.game_number)
		if game.isOver():
			return self.picked_fav and game.favWins() or not(self.picked_fav) and not(game.favWins())
		else:
			return False;

class Monday(models.Model):
	player = models.ForeignKey(User,on_delete=models.CASCADE)
	week_number = models.IntegerField()
	total_points = models.IntegerField(null=True)

	def bonus(self):
		monday_game = Game.objects.filter(week_number=self.week_number).order_by('game_number').last()
		tp = monday_game.totalPoints()
		if tp is None:
			return 0.0
		else:
			return 1 / ( 1 + abs( tp - self.total_points - 0.1 ) )


	def save(self, *args, **kwargs):
		force = False
		try:
			force = kwargs.pop('force')
		except:
			pass
		if not(force) and Game.objects.filter(week_number=self.week_number).order_by('game_number').last().isClosed():
			err = f'Not actually saving. You are trying to change MNTP for a game that isClosed. week: {self.week_number}. If you want to do this use force=True' 
			print(err)
		else:
			super(Monday, self).save(*args, **kwargs)

class Bank(models.Model):
	player = models.ForeignKey(User,on_delete=models.CASCADE)
	deposit_amount = models.FloatField()
	note = models.CharField(max_length=50, default='')
	transaction_date = models.DateTimeField( auto_now=True, blank=False)

class Blog(models.Model):
	entry_date = models.DateTimeField( auto_now=True, blank=False)
	entry = models.CharField(max_length=2048, default='')

class Main(models.Model):
	week_number = models.IntegerField()
	def isOpen(self,current_time = None):
		return Game.objects.get(week_number=self.week_number, game_number = 10).isOpen()
	def isClosed(self,current_time = None):
		return Game.objects.get(week_number=self.week_number, game_number = 10).isClosed()




