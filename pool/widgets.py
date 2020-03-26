from django import forms

class PoolRadio(forms.RadioSelect):
	def __init__(self, *args, **kwargs):
		checked_fav = kwargs.pop('picked_fav')
		spread = kwargs.pop('spread')
		super(PoolRadio, self).__init__(*args, **kwargs)
		self.attrs['checked_fav'] = checked_fav
		self.attrs['spread'] = round(spread - 0.1)

	template_name = 'pool/radio.html'
