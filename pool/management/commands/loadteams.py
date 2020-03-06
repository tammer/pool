from django.core.management.base import BaseCommand, CommandError
from pool.models import Team
import requests
import csv

class Command(BaseCommand):
	help = 'Load the standard teams'

	def handle(self, *args, **options):
		x = input("This will cascade to games, picks, etc.  You sure? [Y/n]")
		# x = 'Y'
		if( x != 'Y' ):
			self.stdout.write("Aborting")
		else:
			Team.objects.all().delete()
			url = 'https://gist.githubusercontent.com/tammer/b5cfda38c1ea1062d2197675bcf8b220/raw/2d77403b87c21caff2bc48f3cddf1f2270c2c041/nfl_teams.csv'
			response = requests.get(url)
			if response.status_code != 200:
				print('Failed to get data:', response.status_code)
			else:
				wrapper = list(csv.reader(response.text.strip().split('\n')))
				wrapper.pop(0)
				for record in wrapper:
					print(record)
					nn = record[1].split(' ')[-1]
					# print(nn)
					cn = record[1].replace(' '+nn,'')
					if cn == 'NY':
						cn = 'New York'
					elif cn == 'LA':
						cn = 'Los Angeles'
					# print(cn)
					Team(full_name = record[1], short_name = record[2], nick_name=nn, city_name=cn).save()