# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
from wfm.models import *
from utils.models import *
from rest_framework import viewsets
from django.contrib.auth.models import User
from .serializers import *


class Shift_ExceptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shift_exceptions to be viewed or edited.
    """
    queryset = Shift_Exception.objects.all()
    serializer_class = Shift_ExceptionSerializer


class Shift_Exception_NoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shift_exception_notes to be viewed or edited.
    """
    queryset = Shift_Exception_Note.objects.all()
    serializer_class = Shift_Exception_NoteSerializer
				
class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows profiles to be viewed or edited.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
				
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
				
class LocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Location to be viewed or edited.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
			
class Skill_LevelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows skill_levels to be viewed or edited.
    """
    queryset = Skill_Level.objects.all()
    serializer_class = Skill_LevelSerializer
				
class Shift_SequenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shift sequences to be viewed or edited.
    """
    queryset = Shift_Sequence.objects.all()
    serializer_class = Shift_SequenceSerializer
				
class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class Event_GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows event groups to be viewed or edited.
    """
    queryset = Event_Group.objects.all()
    serializer_class = Event_GroupSerializer
				
class ShiftViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shifts to be viewed or edited.
    """
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
				
class Day_ModelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows day models to be viewed or edited.
    """
    queryset = Day_Model.objects.all()
    serializer_class = Day_ModelSerializer
			
class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs models to be viewed or edited.
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer
				
class Job_StatusViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs models to be viewed or edited.
    """
    queryset = Job_Status.objects.all()
    serializer_class = Job_StatusSerializer