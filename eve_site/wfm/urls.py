# wfm\shifts\urls.py

from django.conf.urls import url
from wfm import views

urlpatterns = [
	url(r'^calendar/team$', views.calendar_team),
	url(r'^calendar/$', views.calendar),
	url(r'^team_events/$', views.team_events),
	url(r'^resources/$', views.getResources),
	url(r'^events/$', views.events),
	url(r'^user/add$', views.addAgent),
	url(r'^saveevents/(?P<sDate>[-\d]+)/(?P<eDate>[-\d]+)$', views.saveEvents),
	url(r'^schedule_job/$', views.schedule_job),
	url(r'^scheduler/(?P<action>[a-z]+)$', views.scheduler),
	url(r'^add_job/$', views.add_jobs),
]