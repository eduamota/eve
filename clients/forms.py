
from django import forms
from models import Language, Payment_Model, Phone_Number
from django.forms import inlineformset_factory

class ClientForm(forms.Form):
	

	name = forms.CharField(label='Client name', max_length=100)
	branded = forms.BooleanField(label="Custom domain?")
	payments = forms.IntegerField(label="Expected monthly payments")
	hw_support_t1 = forms.BooleanField(label="HW Tier 1 Support?")
	hw_support_t2 = forms.BooleanField(label="HW Tier 2 Support?")
	support_language = forms.ModelMultipleChoiceField(label="Langauges to support", queryset = Language.objects.all())
	domain = forms.CharField(label="HW client domain", max_length=50)
	payment_model = forms.ModelChoiceField(label="Model", queryset = Payment_Model.objects.all())
	wallet_number = forms.CharField(label="WI/IM Number", max_length=15)
	custom_contact_info = forms.BooleanField(label="Require custom contact information?")
	phone_numbers = forms.ModelChoiceField(label="Contact phone Numbers", queryset = Phone_Number.objects.all())
	email_address = forms.EmailField(label="Contact email address")
	chat_float_window = forms.CharField(label="Chat custom window")
	additional_comments = forms.CharField(label="Comments", widget = forms.Textarea)