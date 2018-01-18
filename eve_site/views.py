# -*- coding: utf-8 -*-
"""
Created on Fri Nov 03 12:52:03 2017

@author: emota
"""

from __future__ import unicode_literals

from django.shortcuts import render

def home_page(request):
	
	
	return render(request, 'site/dashboard.html')