# -*- coding: utf-8 -*-
"""
Created on Mon Sep 18 14:28:07 2017

@author: emota
"""

# wfm\shifts\urls.py

from django.conf.urls import url
from clients import views
from views import ClientCreate, ClientUpdate
from django.contrib.auth.decorators import login_required

urlpatterns = [
    url(r'^client/(?P<pk>\d+$)', views.clientInfo, name='client-detail'),
    url(r'^client/$', views.clientInfo, name='client-detail'),
    url(r'^add/', login_required(ClientCreate.as_view()), name='client-add'),
    url(r'^update/(?P<pk>\d+$)', login_required(ClientUpdate.as_view()), name='client-update'),
    url(r'^cost/$', views.contactCostCalculator, name='cost-calculator'),
    url(r'^cost/(?P<action>[\w]+)/$', views.contactCostCalculator, name='cost-calculator'),
    url(r'^cost/(?P<action>[\w]+)/(?P<param>[\w]+)/$', views.contactCostCalculator, name='cost-calculator'),
]