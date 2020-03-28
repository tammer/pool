from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from pool.models import Bank,Blog,Pick,Game,Monday
from pool.widgets import PoolRadio


class MondayForm(ModelForm):
	total_points = forms.IntegerField(label='Monday night total points',widget=forms.NumberInput(attrs={'style':'width: 40px', 'max': '99','min':'0'}))
	class Meta:
		model = Monday
		fields = ['total_points']

class BankForm(ModelForm):

	player = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'), empty_label=None)
	deposit_amount = forms.IntegerField(label='Deposit Amount')
	note = forms.CharField(label='Note', max_length=50)

	class Meta:
		model = Bank
		fields = ['player','deposit_amount','note']

class BlogForm(ModelForm):
	entry = forms.CharField(label='Message', max_length=2048, widget=forms.Textarea)
	# entry_date = forms.DateField()

	class Meta:
		model = Blog
		fields = ['entry']

class PickForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(PickForm, self).__init__(*args, **kwargs)
		if self.instance.game_number is None:
			raise("PickForm created but no game number in the instance.")
		else:
			game = Game.objects.get(game_number=self.instance.game_number, week_number=self.instance.week_number)
			fav = game.favNickName()
			udog = game.udogNickName()
			spread = game.spread
			fav_is_home = game.fav_is_home
			game_date = game.game_date.strftime('%a %-I:%M')
			self.fields['picked_fav'] = forms.ChoiceField(choices=[[True,fav],[False,udog]], widget=PoolRadio(fav_is_home = fav_is_home, game_date = game_date, spread = spread, picked_fav=self.instance.picked_fav), label='')
			self.fields['picked_fav'].disabled = game.isClosed()


	week_number = forms.CharField(widget=forms.HiddenInput())
	game_number = forms.CharField(widget=forms.HiddenInput())

	class Meta:
		model = Pick
		fields = ['picked_fav','week_number','game_number']


class SpreadForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(SpreadForm, self).__init__(*args, **kwargs)
		self.fav = Game.objects.get(game_number=self.instance.game_number, week_number=self.instance.week_number).favFullName()
		self.udog = Game.objects.get(game_number=self.instance.game_number, week_number=self.instance.week_number).udogFullName()

	spread = forms.IntegerField(label='',widget=forms.NumberInput(attrs={'style':'width: 45px', 'max': '99','min':'-99'}))

	class Meta:
		model = Game
		fields = ['spread']
