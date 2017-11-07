# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 20:23:16 2017

@author: _emota
"""

# wfm\shifts\urls.py

from django.conf.urls import url
from phone import views

urlpatterns = [
	url(r'^agents/$', views.agents),
	url(r'^queues/$', views.queues),
	url(r'^agents/(?P<agentid>\w+)', views.agents),
	url(r'^queues/(?P<queueid>[a-z\d]+$)', views.queues),
]