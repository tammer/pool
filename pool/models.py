from django.db import models
from django.contrib.auth.models import User
import datetime
from pytz import timezone

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
	spread = models.FloatField( null=True )
	game_date = models.DateTimeField()
	fav_score = models.IntegerField( null=True )
	udog_score = models.IntegerField( null=True )
	fav_is_home = models.BooleanField()
	is_final = models.BooleanField( default = False )
	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['week_number', 'game_number'], name='unique_week_game'),
			#spread >=0
		]
	
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


	def isClosed(self, current_time = None):
		if current_time is None:
			current_time = datetime.datetime.now(self.game_date.tzinfo)
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

	def game(self):
		return Game.objects.get(week_number=self.week_number, game_number=self.game_number)

	def whoShortName(self):
		if self.picked_fav:
			return self.game().favShortName()
		else:
			return self.game().udogShortName()

	def isCorrect(self):
		game = Game.objects.get(week_number=self.week_number, game_number=self.game_number)
		# throw something if game.final() == False
		return self.picked_fav and game.favWins() or not(self.picked_fav) and not(game.favWins())

class Monday(models.Model):
	player = models.ForeignKey(User,on_delete=models.CASCADE)
	week_number = models.IntegerField()
	total_points = models.IntegerField()

class Bank(models.Model):
	player = models.ForeignKey(User,on_delete=models.CASCADE)
	deposit_amount = models.FloatField()

class Main(models.Model):
	week_number = models.IntegerField()
	def isOpen(self,current_time = None):
		return Game.objects.get(week_number=self.week_number, game_number = 10).isOpen()
	def isClosed(self,current_time = None):
		return Game.objects.get(week_number=self.week_number, game_number = 10).isClosed()




