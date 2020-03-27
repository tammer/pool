from django import forms

class PoolRadio(forms.RadioSelect):
	def __init__(self, *args, **kwargs):
		checked_fav = kwargs.pop('picked_fav')
		spread = kwargs.pop('spread')
		game_date = kwargs.pop('game_date')
		super(PoolRadio, self).__init__(*args, **kwargs)
		self.attrs['checked_fav'] = checked_fav
		if spread is None:
			self.attrs['spread'] = 'na'
		else:
			self.attrs['spread'] = round(spread - 0.1)
		self.attrs['game_date'] = game_date

	template_name = 'pool/radio.html'
