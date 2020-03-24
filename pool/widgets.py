from django import forms

class PoolRadio(forms.RadioSelect):
	def __init__(self, *args, **kwargs):
		game_number = kwargs.pop('game_number')
		super(PoolRadio, self).__init__(*args, **kwargs)
		self.attrs['game_number'] = game_number

	template_name = 'pool/radio.html'
