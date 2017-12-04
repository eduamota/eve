# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 20:23:16 2017

@author: _emota
"""

# wfm\shifts\urls.py

from django.conf.urls import url
from otrs_connector import views

urlpatterns = [
    url(r'^Ticket/(?P<ticketid>\d+$)', views.ticket),
]