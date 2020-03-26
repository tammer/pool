from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from pool.models import Bank,Blog,Pick,Game
from pool.widgets import PoolRadio



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
			self.fields['picked_fav'] = forms.ChoiceField(choices=[[True,fav],[False,udog]], widget=PoolRadio(spread = spread, picked_fav=self.instance.picked_fav), label='')


	week_number = forms.CharField(widget=forms.HiddenInput())
	game_number = forms.CharField(widget=forms.HiddenInput())

	class Meta:
		model = Pick
		fields = ['picked_fav','week_number','game_number']
