# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Location(models.Model):
    name = models.CharField(max_length=50)
    iso_name = models.CharField(max_length=50)

    def __str__(self):              # __unicode__ on Python 2
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):              # __unicode__ on Python 2
        return self.name

class Skill_Level(models.Model):
    level = models.DecimalField(max_digits=3, decimal_places=0)
    skill = models.OneToOneField(Skill, on_delete=models.CASCADE)
    def __str__(self):              # __unicode__ on Python 2
        return str(self.level) + " " + str(self.skill)

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team_manager = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='team_manager', blank=True)
    employee_number = models.SmallIntegerField(blank=True)
    extension = models.SmallIntegerField(blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, blank=True)
    label = models.CharField(max_length=150, blank=True)
    skill_level = models.ManyToManyField(Skill_Level, blank=True)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.user.first_name) + " " + str(self.user.last_name)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

class Notification(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    from_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='from_user', blank=True, null=True)
    message = models.CharField(max_length=500)
    view = models.BooleanField()
