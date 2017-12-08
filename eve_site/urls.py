"""eve_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from eve_site import views
from rest_framework import routers
from api1_0 import views as apiViews

router = routers.DefaultRouter()
router.register(r'shift_exception', apiViews.Shift_ExceptionViewSet)
router.register(r'shift_exception_note', apiViews.Shift_Exception_NoteViewSet)
router.register(r'profile', apiViews.ProfileViewSet)
router.register(r'user', apiViews.UserViewSet)
router.register(r'location', apiViews.LocationViewSet)
router.register(r'skill_level', apiViews.Skill_LevelViewSet)
router.register(r'shift_sequence', apiViews.Shift_SequenceViewSet)
router.register(r'event', apiViews.EventViewSet)
router.register(r'event_group', apiViews.Event_GroupViewSet)
router.register(r'shift', apiViews.ShiftViewSet)
router.register(r'day_model', apiViews.Day_ModelViewSet)
router.register(r'job', apiViews.JobViewSet)
router.register(r'job_status', apiViews.Job_StatusViewSet)

urlpatterns = [
	url(r'^api/', include(router.urls)),
	url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
	url(r'^admin/', admin.site.urls),
	url(r'^dashboard/', views.dashboard),
	url(r'^phone/', include('phone.urls')),
	url(r'^accounts/login/$', auth_views.LoginView.as_view(), name="login"),
	url(r'^accounts/logout/$', auth_views.LogoutView.as_view(), {'next_page': '/accounts/login/',}),
	url(r'^api/otrs/', include('otrs_connector.urls')),
	url(r'^quality/', include('quality.urls')),
	url(r'^wfm/', include('wfm.urls')),
	url(r'^$', views.dashboard),
]
