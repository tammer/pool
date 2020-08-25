from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import json

# Will only be used once!

class Command(BaseCommand):

	def handle(self, *args, **options):
		User.objects.all().delete()
		with open('players.json') as f:
			data = json.load(f)
		for row in data[2]['data']:
			if row['playerName'] != 'MASTER':
				print(row['playerName'])
				username = row['playerName']
				email = row['username']
				pw = row['password']
				if username == 'Mike Leroux':
					username = 'MikeL'
				if username == 'Tammer':
					User.objects.create_user(username,email,pw,is_superuser=True,is_staff=True)
				else:
					User.objects.create_user(username,email,pw,is_superuser=False)
