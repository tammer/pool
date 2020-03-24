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

class PicksForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(PicksForm, self).__init__(*args, **kwargs)
		fav = Game.objects.get(game_number=self.instance.game_number, week_number=self.instance.week_number).fav.nick_name
		udog = Game.objects.get(game_number=self.instance.game_number, week_number=self.instance.week_number).udog.nick_name
		self.fields['picked_fav'] = forms.ChoiceField(choices=[[True,fav],[False,udog]], widget=PoolRadio(game_number=self.instance.game_number), label='')

	class Meta:
		model = Pick
		fields = ['picked_fav']
