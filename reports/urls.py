# wfm\shifts\urls.py

from django.conf.urls import url
from reports import views

urlpatterns = [
	url(r'^gap_analysis/$', views.gap_analysis),
	url(r'^get_heatmap_data/$', views.get_heatmap_data),
]
