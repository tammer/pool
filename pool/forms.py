from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from pool.models import Bank,Blog



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