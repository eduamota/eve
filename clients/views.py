# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponseRedirect

from .forms import ClientForm

# Create your views here.
def client(request):
		# if this is a POST request we need to process the form data
	if request.method == 'POST':
        # create a form instance and populate it with data from the request:
		form = ClientForm(request.POST)
        # check whether it's valid:
		if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
			return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
	else:
		form = ClientForm()

	return render(request, 'client/default.html', {'form': form})