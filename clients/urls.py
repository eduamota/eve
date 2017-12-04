# -*- coding: utf-8 -*-
"""
Created on Mon Sep 18 14:28:07 2017

@author: emota
"""

# wfm\shifts\urls.py

from django.conf.urls import url
from clients import views

urlpatterns = [
    url(r'^client/$', views.client),
]