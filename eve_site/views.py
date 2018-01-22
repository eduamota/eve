# -*- coding: utf-8 -*-
"""
Created on Fri Nov 03 12:52:03 2017

@author: emota
"""

from __future__ import unicode_literals
import requests
from django.shortcuts import render

def home_page(request):
	
	
	return render(request, 'site/dashboard.html')
	
def agent_dashboard(request):
	req =	 requests.get("http://10.5.225.93/jasperserver/rest_v2/reports/Personal_Stats/Agent_Contact_Stats.html?Start_Date=2018-01-11&End_Date=2018-01-17&LoggedInUserEmailAddress=lgarcia@hyperwallet.com", auth=('emota','L!$e)&abby12'))
	js = req.text
	return render(request, 'site/agent_dashboard.html', {"stats":js})