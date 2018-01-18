# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from models import Client, Client_Info, Comment
from django.views.generic.edit import CreateView, UpdateView
from .forms import ClientForm, AddComment
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.


class ClientCreate(CreateView):
	model = Client
	fields = ['name']

class ClientUpdate(UpdateView):
	model = Client
	fields = ['name']

@login_required
def clientInfo(request, pk = 0):
	if request.method == "GET":
		if pk > 0:
			cl = Client.objects.get(pk = pk)
			try:
				client_i = Client_Info.objects.get(client = cl)
			except ObjectDoesNotExist:
				client_i = Client_Info(client = cl, branded = False, hw_support_t1 = False, hw_support_t2 = False, custom_contact_info = False, change_by = request.user)
				client_i.save()
			
			form = ClientForm(instance=client_i, initial={'change_by': request.user})
			form2 = AddComment(initial={'change_by': request.user, 'client': cl})
			
			try:
				comments = Comment.objects.filter(client = cl)
				return render(request, 'clients/default.html', {'form': form, 'form2': form2, 'comm':comments})
			except ObjectDoesNotExist:
				return render(request, 'clients/default.html', {'form': form, 'form2': form2})
		else:
			form = ClientForm(initial={'change_by': request.user})
			form2 = AddComment(initial={'change_by': request.user})
	
			return render(request, 'clients/default.html', {'form': form, 'form2': form2})
			
		# if this is a POST request we need to process the form data
	elif request.method == 'POST':
		cl = Client.objects.get(pk = pk)
		c_i = Client_Info.objects.get(client = cl)
        # create a form instance and populate it with data from the request:
		form = ClientForm(request.POST, instance=c_i, initial={'change_by': request.user})
		form.instance.change_by = request.user
		
		form2 = AddComment(request.POST)
		
        # check whether it's valid:
		if form.is_valid() or form2.is_valid():
			form.save()
			form2.save()
			try:
				comments = Comment.objects.filter(client = cl)
				return render(request, 'clients/default.html', {'form': form, 'form2': form2, 'comm':comments})
			except ObjectDoesNotExist:
				return render(request, 'clients/default.html', {'form': form, 'form2': form2})
    # if a GET (or any other method) we'll create a blank form
	else:
		form = ClientForm(initial={'change_by': request.user})
		form2 = AddComment(initial={'change_by': request.user})

		return render(request, 'clients/default.html', {'form': form, 'form2': form2})

	