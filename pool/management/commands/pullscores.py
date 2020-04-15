from django.core.management.base import BaseCommand, CommandError
from pool.utils import implied_week,set_score
import json, requests

class Command(BaseCommand):
	help = 'Pull the latest scores'

	def handle(self, *args, **options):
		week_number = implied_week()
		url = 'http://www.nfl.com/liveupdate/scores/scores.json'
		response = requests.get(url)
		if response.status_code != 200:
			print('Failed to get data:', response.status_code)
		else:
			scores = json.loads(response.text)
			for game in scores.values():
				if game['qtr'] != 'Final':
					continue
				t1 = game['home']['abbr']
				s1 = game['home']['score']['T']
				t2 = game['away']['abbr']
				s2 = game['away']['score']['T']
				result = {t1:s1, t2:s2}
				print(result)
				set_score(week_number,result)
