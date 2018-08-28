# wfm\shifts\urls.py

from django.conf.urls import url
from reports import views

urlpatterns = [
	url(r'^reports/gap_analysis$', views.gap_analysis),
]
