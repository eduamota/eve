# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
def ticket(request, ticketid):
	
	f = open('test.txt', 'w')
	f.write(ticketid)
	for key, value in request.POST.items():
		f.write(key)
		f.write(value)
	f.close()
	response = {"TicketNumber":"12", "InvokerType":"Create"}
	return JsonResponse(response, safe=False)
