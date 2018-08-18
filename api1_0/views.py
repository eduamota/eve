# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
from wfm.models import *
from utils.models import *
from quality.models import *
from rest_framework import viewsets
from django.contrib.auth.models import User
from .serializers import *


class Shift_ExceptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shift_exceptions to be viewed or edited.
    """
    queryset = Shift_Exception.objects.all()
    serializer_class = Shift_ExceptionSerializer

    #def partial_update(self, instance, validated_data):
    def perform_update(self, serializer):
        instance = serializer.save()
        st = instance.status
        ev_id = instance.event
        from_dt = instance.start_date_time
        to_dt = instance.end_date_time
        profile = instance.user
        cuser = instance.actioned_by

        ev = ev_id.name
        no_valid_shift = False
        if st == 1 and "Overtime" in ev:
            sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__lte = from_dt).filter(end_date_time__gte = to_dt)
            if len(sh_f) == 0:
                no_valid_shift = True

            if no_valid_shift:
                sf_f_s = Shift_Sequence.objects.filter(user = profile).filter(start_date_time = to_dt)
                if len(sf_f_s) > 0:
                    sf_f_s[0].start_date_time = from_dt
                    sf_f_s[0].save()

                sf_f_e = Shift_Sequence.objects.filter(user = profile).filter(end_date_time = from_dt)
                if len(sf_f_e) > 0:
                    sf_f_e[0].end_date_time = to_dt
                    sf_f_e[0].save()

                sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__lte = from_dt).filter(end_date_time__gte = to_dt)

                if len(sh_f) == 0:
                    sh_f_n = Shift_Sequence(user = profile, start_date_time = from_dt, start_diff = 0, end_date_time = to_dt, end_diff = 0, actioned_by = cuser)
                    sh_f_n.save()

            sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__lte = from_dt).filter(end_date_time__gte = to_dt)[0]
            instance.shift_sequence = sh_f
            instance.approved = True
            instance.save()
        elif (st == 2 or st == 3)  and "Overtime" in ev:
            instance.shift_sequence = None
            instance.approved = False
            instance.save()
            sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__lte = from_dt).filter(end_date_time__gte = to_dt)
            for sh in sh_f:
            #print(sh_f)
                if sh.start_date_time == from_dt and sh.end_date_time == to_dt:
                    sh.delete()
                elif sh.start_date_time == from_dt and sh.end_date_time >= to_dt:
                    sh.start_date_time = to_dt
                    sh.save()
                elif sh.start_date_time <= from_dt and sh.end_date_time == to_dt:
                    sh.end_date_time = from_dt
                    sh.save()
        elif (st== 1):
            instance.approved = True
            instance.save()
        else:
            instance.approved = False
            instance.save()
        instance.save()


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

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows notification models to be viewed or editedself.
    """
    queryset = Notification.objects.all()
    serializer_class = Notification

class Form_OverviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows quality fomrs models to be viewed or edited
    """
    queryset = Form_Overview.objects.all()
    serializer_class = Form_Overview
