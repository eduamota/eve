# wfm\shifts\urls.py

from django.conf.urls import url
from wfm import views

urlpatterns = [
    url(r'^calendar/$', views.calendar),
]