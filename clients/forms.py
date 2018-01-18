
from django import forms
from django.forms import ModelForm
from models import Comment, Client, Client_Info


class ClientForm(ModelForm):
	
	class Meta:
		model = Client_Info
		fields = '__all__'
		labels = {'client': 'Client Name', 'branded': 'Custom domain?', 'hw_support_t1': 'HW doing T1?', 'hw_support_t2': 'HW doing T2?', 'support_language': 'Languages to support', 'domain': 'HW client domain', 'payment_model': 'Model', 'wallet_numner': 'WI/MI number', 'custom_contact_info': 'Requires custom contact info?', 'phone_numbers': 'Phone Numbers', 'email_adress': 'Support email', 'chat_float_window':'Chat Window ID', 'additional_comments': 'Comments / Notes', 'first_registration': 'Date of first registration', 'first_payment':'Date of first payment'}

		widgets = {'client': forms.Select(attrs={'onchange':  "changeClient(this)"}),'additional_comments': forms.Textarea, 'first_registration': forms.DateInput(attrs={'type': 'date'}), 'first_payment': forms.DateInput(attrs={'type': 'date'}), 'change_by': forms.HiddenInput}
		
		
class AddComment(ModelForm):
	class Meta:
		model = Comment
		fields = '__all__'
		
		labels = {'comments':'Comments  / Notes'}
		
		widgets = {'client': forms.HiddenInput, 'change_by': forms.HiddenInput}