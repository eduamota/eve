# -*- coding: utf-8 -*-
"""
Created on Thu Dec 07 12:32:46 2017

@author: emota
"""

from wfm.models import *
from utils.models import *
from django.contrib.auth.models import User
from rest_framework import serializers


class Shift_ExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift_Exception
        fields = ('id', 'user', 'shift_sequence', 'event', 'start_date_time', 'start_diff', 'end_date_time', 'end_diff', 'submitted_time', 'actioned_time', 'actioned_by', 'status', 'approved')

class Shift_Exception_NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift_Exception_Note
        fields = ('id', 'shift_exception', 'note', 'created_by', 'created_time')

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'user', 'team_manager', 'employee_number', 'extension', 'location', 'label', 'skill_level')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active' )

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'iso_name')

class Skill_LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill_Level
        fields = ('id', 'level', 'skill')

class Shift_SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift_Sequence
        fields = ('id', 'user', 'start_date_time', 'start_diff', 'end_date_time', 'end_diff', 'actioned_time', 'actioned_by')

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'name', 'group', 'color', 'text_color', 'paid')

class Event_GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event_Group
        fields = ('id', 'name',)

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ('id', 'user', 'day_model', 'valid_from', 'valid_to', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday')

class Day_ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Day_Model
        fields = ('id', 'name', 'day_start_time', 'day_start_diff', 'day_end_time', 'day_end_diff', 'time_zone')

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('id', 'job_type', 'from_date', 'to_date', 'agents', 'status', 'parameters', 'actioned_time', 'actioned_by')

class Job_StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job_Status
        fields = ('id', 'name')
