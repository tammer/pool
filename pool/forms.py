from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from pool.models import Bank



class BankForm(ModelForm):

	player = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'), empty_label=None)
	deposit_amount = forms.IntegerField(label='Deposit Amount')
	note = forms.CharField(label='Note', max_length=50)

	class Meta:
		model = Bank
		fields = ['player','deposit_amount','note']
