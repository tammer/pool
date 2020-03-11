from django.core.management.base import BaseCommand, CommandError
from pool.models import Pick,Game,Bank
from django.contrib.auth.models import User
from random import choice


class Command(BaseCommand):
	help = 'Put some money in the bank'

	def handle(self, *args, **options):

		x = input("This will wreck the bank Y/n")

		if x != 'Y':
			print("Aborting")
			exit()

		for user in User.objects.all():
			notes = ["you have to allow for null values","file associated with this instance","may be unnecessary to call"]
			Bank.objects.create(player=user, deposit_amount = choice([-75,50,50,50,50,50]), note = choice(notes))

		