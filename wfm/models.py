# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from utils.models import Profile

class Day_Model(models.Model):
    name = models.CharField(max_length=40)
    day_start_time = models.TimeField(default='06:00:00')
    day_start_diff = models.DecimalField(max_digits=1, decimal_places=0, default=0)
    day_end_time = models.TimeField(default='14:30:00')
    day_end_diff = models.DecimalField(max_digits=1, decimal_places=0, default=0)
    time_zone = models.CharField(max_length=50, blank=True)

    def __str__(self):              # __unicode__ on Python 2
        return (self.name + " " + self.time_zone)

class Job_Status(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
       return self.name

class Job(models.Model):
    job_type = models.CharField(max_length=20)
    from_date = models.DateTimeField()
    to_date = models.DateTimeField()
    agents = models.TextField()
    status = models.ForeignKey(Job_Status, on_delete=models.CASCADE, blank=True, default=None)
    parameters = models.CharField(max_length=200, blank=True, default=None)
    actioned_time = models.DateTimeField(default=timezone.now, blank=True)
    actioned_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, default=None)

    def __str__(self):              # __unicode__ on Python 2
        return "%s %s" % (str(self.job_type), str(self.actioned_time))

class Shift(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    day_model = models.ForeignKey(Day_Model, on_delete=models.CASCADE)
    valid_from = models.DateField(default="2017-01-01")
    valid_to = models.DateField(default="2017-12-31")
    sunday = models.BooleanField(default=False)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)

    def __str__(self):              # __unicode__ on Python 2
        return "%s %s" % (str(self.user), str(self.day_model))

class Shift_Sequence(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    start_date_time = models.DateTimeField()
    start_diff = models.DecimalField(max_digits=1, decimal_places=0)
    end_date_time = models.DateTimeField()
    end_diff = models.DecimalField(max_digits=1, decimal_places=0)
    actioned_time = models.DateTimeField(default=timezone.now, blank=True)
    actioned_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, default=None)

    def __str__(self):
        return str(self.user) + " - From: " + str(self.start_date_time) + " To: " + str(self.end_date_time)

class Event_Group(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):              # __unicode__ on Python 2
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=40)
    group = models.ForeignKey(Event_Group, on_delete=models.CASCADE)
    color = models.CharField(max_length=7)
    text_color = models.CharField(max_length=7)
    paid = models.BooleanField()

    def __str__(self):              # __unicode__ on Python 2
        return self.name

class Shift_Exception(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    shift_sequence = models.ForeignKey(Shift_Sequence, on_delete=models.CASCADE, blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_date_time = models.DateTimeField()
    start_diff = models.DecimalField(max_digits=1, decimal_places=0)
    end_date_time = models.DateTimeField()
    end_diff = models.DecimalField(max_digits=1, decimal_places=0)
    approved = models.BooleanField(default=True)
    submitted_time = models.DateTimeField(default=timezone.now)
    actioned_time = models.DateTimeField(default=timezone.now, blank=True)
    actioned_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, default=None)
    status = models.DecimalField(max_digits=1, decimal_places=0, default=0)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.event)

class Shift_Exception_Note(models.Model):
    shift_exception = models.ForeignKey(Shift_Exception, on_delete=models.CASCADE)
    note = models.TextField()
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=timezone.now)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.created_by.user.first_name) + " " + str(self.created_by.user.last_name)

class Log_Type(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name)

class Log(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=timezone.now)
    shift_sequence = models.ForeignKey(Shift_Sequence, on_delete=models.CASCADE, blank=True, default=None)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, default=None)
    log_type = models.ForeignKey(Log_Type, on_delete=models.CASCADE)
    log_info = models.TextField()

    def __str__(self):              # __unicode__ on Python 2
        return self.event_type.name + " " + self.created_by.first_name

class vacation_tracker(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    added_date_time = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=5, decimal_places=3, default=0)
    description = models.CharField(max_length=250)

    def __str__(self):
        return self.profile__user__first_name + " " + self.profile__user__last_name + " " + self.description + " " + self.description
