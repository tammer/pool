from django.core.management.base import BaseCommand, CommandError
from pool.utils import backup


class Command(BaseCommand):
	help = 'Backs up the database to backups/'

	def handle(self, *args, **options):
		backup()