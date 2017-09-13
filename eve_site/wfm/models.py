# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
# Create your models here.
    
class Location(models.Model):
    name = models.CharField(max_length=50)
    iso_name = models.CharField(max_length=50)
    
    def __str__(self):              # __unicode__ on Python 2
        return self.name
    
class Role(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):              # __unicode__ on Python 2
        return self.name
        
class Skill(models.Model):
    name = models.CharField(max_length=50)
    level = models.DecimalField(max_digits=3	, decimal_places=0)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_number = models.SmallIntegerField(blank=True)
    extension = models.SmallIntegerField(blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, blank=True)
    label = models.CharField(max_length=150, blank=True)
    skill = models.ManyToManyField(Skill, blank=True)
    
    def __str__(self):              # __unicode__ on Python 2
        return str(self.user)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)
            
    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

class Day_Model(models.Model):
    name = models.CharField(max_length=40)
    day_start_time = models.TimeField(default='06:00:00')
    day_start_diff = models.DecimalField(max_digits=1, decimal_places=0, default=0)
    day_end_time = models.TimeField(default='14:30:00')
    day_end_diff = models.DecimalField(max_digits=1, decimal_places=0, default=0)
    
    def __str__(self):              # __unicode__ on Python 2
        return self.name

class Shift(models.Model):
    user = models.OneToOneField(Profile)
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
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_date_time = models.DateTimeField()
    start_diff = models.DecimalField(max_digits=1, decimal_places=0)
    end_date_time = models.DateTimeField()
    end_diff = models.DecimalField(max_digits=1, decimal_places=0)
    actioned_time = models.DateTimeField(default=timezone.now, blank=True)
    actioned_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, default=None)
    approved = models.BooleanField(default=False)
    
    