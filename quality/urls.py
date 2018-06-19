# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 20:23:16 2017

@author: _emota
"""

# wfm\shifts\urls.py

from django.conf.urls import url
from quality import views

urlpatterns = [
	url(r'^form/search', views.formSearch),
	url(r'^form$', views.formAction),
	url(r'^form/new', views.formAction),
	url(r'^form/(?P<form>\d+$)', views.formAction),
	url(r'^form/v2/search', views.formSearchv2),
	url(r'^form/v2/$', views.formActionv2),
	url(r'^form/v2/new', views.formActionv2),
	url(r'^form/v2/(?P<form>\d+$)', views.formActionv2)
]
