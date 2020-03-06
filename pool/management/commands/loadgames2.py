from django.core.management.base import BaseCommand, CommandError
from pool.models import Team,Game
import requests
import xml.etree.ElementTree as ET
import datetime

class Command(BaseCommand):
	help = 'Load the standard teams'

	def handle(self, *args, **options):

		this_year = 2019 # make this a command line input

		Game.objects.all().delete()

		for x in range(17):
			week_number = x+1
			url = 'http://www.nfl.com/ajax/scorestrip?season='+str(this_year)+'&seasonType=REG&week='+str(week_number)
			response = requests.get(url)
			if response.status_code != 200:
				print('Failed to get data:', response.status_code)
			else:
				root = ET.fromstring(response.text)
				i=0
				for gm in root[0]:
					
					print(gm.attrib)
					hour = int(root[0][i].attrib['t'].split(':')[0])
					if hour < 12:
						hour += 12 # !!! Totally fails if the game is actually in the morning

					gm_dt = datetime.datetime(int(root[0][i].attrib['eid'][0:4]),
						int(root[0][i].attrib['eid'][4:6]),
						int(root[0][i].attrib['eid'][6:8]),
						hour,
						int(root[0][i].attrib['t'].split(':')[1])
						)
					
					Game.objects.create(
						week_number = week_number, game_number=i+1,
						fav = Team.objects.get(short_name=gm.attrib['h']),
						udog = Team.objects.get(short_name=gm.attrib['v']),
						game_date = gm_dt,
						fav_is_home = True)
					i=i+1

		print("!!! Any games that are actually in the morning are going to wrong !!!!")
