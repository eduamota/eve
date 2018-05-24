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


def contactCostCalculator(request, action = None, param = None):

	if action == "channel" and request.method == "GET":
		size = param
		return render(request, 'clients/client_cost_channel.html', {'size': int(size)})
	elif action == "language" and request.method == "POST":
		#print(request.POST)
		size = request.POST['size']
		channels = []
		if 'phone' in request.POST:
			channels.append('phone')
		if 'chat' in request.POST:
			channels.append('chat')
		if 'email' in request.POST:
			channels.append('email')

		return render(request, 'clients/client_cost_language.html', {'channels': channels, 'size': size})
	elif action == "hours" and request.method == "POST":

		languages = {}
		size = request.POST['size']

		hc_multi = 1

		hc_multi = int(size)/22/5/45
		#print(hc_multi)
		if int(size) > 70000 and hc_multi < 7:
			hc_multi = 7

		language_count = 0

		for field, value in request.POST.items():
			if "english" in field or "spanish" in field or "french" in field:
				parts = field.split('-')
				language_count += 1
				multiplier = 1

				if parts[1] == "spanish" or parts[1] == "french":
					multiplier = 2

				if parts[0] not in languages:
					languages[parts[0]] = {}
				if parts[0] == 'phone':
					languages[parts[0]][parts[1]] = 120 * multiplier
				elif parts[0] == 'email':
					languages[parts[0]][parts[1]] = 50 * multiplier
				elif parts[0] == 'chat':
					languages[parts[0]][parts[1]] = 70 * multiplier
				else:
					languages[parts[0]][parts[1]] = 120 * multiplier
			elif "premium" in field:

				parts = field.split('-')
				if parts[0] not in languages:
					languages[parts[0]] = {}
				for i in range(0, int(value)):
					language_count += 1
					languages[parts[0]]["premium_" + str(i+1)] = 500


		#hc_multi = hc_multi

		if hc_multi < 1:
			hc_multi = 1

		for c, v in languages.items():
			for l, co in v.items():
				languages[c][l] = co*hc_multi

		return render(request, 'clients/client_cost_hours.html', {'languages': languages, 'size': size})
	elif action =="summary" and request.method == "POST":

		size = request.POST['size']

		hc_multi = 1

		hc_multi = int(size)/22/5/45
		#print(hc_multi)
		if int(size) > 70000 and hc_multi < 7:
			hc_multi = 7

		hc_multi = 1-(hc_multi/100)


		support = {}
		support_cost = 0
		additional_cost = {"Training":"500", "Standard Reporting":"1000", "Custom Reporting per hour":"120"}
		phone_additional_cost = {"North_America": "0", "France": str(hc_multi*200), "Spain": str(hc_multi*200), "UK": str(hc_multi*200), "Germany": str(hc_multi*200)}

		if size < 10000:
				del phone_additional_cost['North_America']
				phone_additional_cost['North_America_Custom'] = "100"

		for field, value in request.POST.items():
			if "weekend" in field or "weekday" in field:
				parts = field.split("-")
				section = parts[0] + " " + parts[1]
				if section not in support:
					support[section] = {}
				hours = parts[2] + " " + parts[3]
				support[section][hours] = value
				support_cost += int(value)

		return render(request, 'clients/client_cost_summary.html', {"size": size, "support":support, "cost":support_cost, "additional_service":additional_cost, "phone_additional_service": phone_additional_cost})

	else:
		return render(request, 'clients/client_cost_size.html')
