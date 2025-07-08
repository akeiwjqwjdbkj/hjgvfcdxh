
import datetime

from django import forms
from django.forms import ModelForm

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import BookInstance

class RenewBookForm(forms.Form):
	renewal_date = forms.DateField(help_text='Enter a date between now and 4 weeks (default 3).')

	def clean_renewal_date(self):
		data = self.cleaned_data['renewal_date']

		# Verify date is NOT in the past
		if data < datetime.date.today():
			raise ValidationError(_('Invalid date - renewal in past'))
		
		# Verify date is in the allowed range (over: >4 weeks from today)
		if data > datetime.date.today() + datetime.timedelta(weeks=4):
			raise ValidationError(_('Invalid date - renewal more than 4 weeks'))
		
		# *** Return cleaned data
		return data

class RenewBookModelForm(ModelForm):
	def clean_due_back(self):
		data = self.cleaned_data['due_back']

		# Verify date is NOT in the past
		if data < datetime.date.today():
			raise ValidationError(_('Invalid date - renewal in past'))
		
		# Verify date is in the allowed range (over: >4 weeks from today)
		if data > datetime.date.today() + datetime.timedelta(weeks=4):
			raise ValidationError(_('Invalid date - renewal more than 4 weeks'))

		return data

	class Meta:
		model = BookInstance
		fields = [ 'due_back' ]
		# mark the due_back field as the renewal date
		labels = { 'due_back' : _('New renewal date') }
		help_texts = { 'due_back' : _('Enter a date between now and 4 weeks (default 3).') }
