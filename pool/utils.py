from pool.models import Team,Game,Pick,Bank,Blog,Monday,now
from django.contrib.auth.models import User

def add_player(username,email,pw):
	if User.objects.filter(username=username).exists():
		raise( NameError(f'{username} exists already'))
	User.objects.create_user(username,email,pw)
	init_player(username)

# This function assumes games are loaded
def init_player(username):
	user = User.objects.get(username=username)
	Pick.objects.filter(player=user).delete()
	for game in Game.objects.all():
		pick = Pick(week_number=game.week_number, game_number=game.game_number, player=user,picked_fav=True)
		pick.save(force=True)
	for game in Game.objects.filter(game_number=1):
		monday = Monday(week_number=game.week_number,player=user,total_points=0)
		monday.save(force=True)

def delete_player(username):
	if not(User.objects.filter(username=username).exists()):
		raise( NameError(f'{username} does not exist'))
	user = User.objects.get(username=username)
	Monday.objects.filter(player=user).delete()
	Pick.objects.filter(player=user).delete()
	user.delete()

