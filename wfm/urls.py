# wfm\shifts\urls.py

from django.conf.urls import url
from wfm import views

urlpatterns = [
	url(r'^calendar/team$', views.calendar_team),
	url(r'^calendar/$', views.calendar),
	url(r'^team_events/$', views.team_events),
	url(r'^manage_events/$', views.manage_events),
	url(r'^manage_exceptions/$', views.manage_exceptions),
	url(r'^resources/$', views.getResources),
	url(r'^events/$', views.events),
	url(r'^schedule_job/$', views.schedule_job),
	url(r'^settz/$', views.set_timezone),
	url(r'^request/(?P<ev>[a-zA-Z]+)$', views.add_event),
	url(r'^request/$', views.add_event),
	url(r'^manager/request/(?P<ev>[a-zA-Z]+)$', views.add_request_manager),
	url(r'^manager/request/$', views.add_request_manager),
	url(r'^review/requests/$', views.review_requests),
	url(r'^agent/$', views.agentBoard),
	url(r'^change/$', views.changeException),
	url(r'^add/$', views.addEvent),
	url(r'^calendar/manage/$', views.calendar_manage),
]
