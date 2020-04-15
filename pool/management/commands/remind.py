from django.core.management.base import BaseCommand, CommandError
from pool.models import Monday,Game
from pool.utils import status,now
from django.contrib.auth.models import User
from django.core.mail import send_mail

class Command(BaseCommand):
	help = 'Sends out reminder emails to anyone who has not done their picks'

	def handle(self, *args, **options):
		(week_number,state) = status()
		if state != 'Open':
			return
		if now() > Game.objects.all().order_by('week_number','game_number').last().game_date:
			return
		for m in Monday.objects.filter(week_number=week_number,total_points=0):
			user = m.player
			if user.email is not '':
				send_mail('Reminder: Do your picks','http://pool.tammer.com/dopicks/','pool@tammer.com',[user.email],fail_silently=False)
