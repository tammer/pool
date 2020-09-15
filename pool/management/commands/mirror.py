from django.core.management.base import BaseCommand, CommandError
from pool.utils import rebuild



class Command(BaseCommand):
	help = 'Makes dev db look like production'

	def handle(self, *args, **options):
		rebuild('.')
		