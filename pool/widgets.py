from django import forms

class PoolRadio(forms.RadioSelect):
	def __init__(self, *args, **kwargs):
		checked_fav = kwargs.pop('picked_fav')
		spread = kwargs.pop('spread')
		game_date = kwargs.pop('game_date')
		fav_is_home = kwargs.pop('fav_is_home')
		super(PoolRadio, self).__init__(*args, **kwargs)
		self.attrs['checked_fav'] = checked_fav
		if spread is None:
			self.attrs['spread'] = 'na'
		else:
			self.attrs['spread'] = spread
		self.attrs['game_date'] = game_date
		self.attrs['fav_is_home'] = fav_is_home

	template_name = 'pool/radio.html'
