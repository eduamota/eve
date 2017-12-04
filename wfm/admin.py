# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Location, Role, Profile, Shift, Day_Model, Event_Group, Event, Shift_Exception, Skill

admin.site.register(Location)
admin.site.register(Role)
admin.site.register(Profile)
admin.site.register(Shift)
admin.site.register(Day_Model)
admin.site.register(Event_Group)
admin.site.register(Event)
admin.site.register(Shift_Exception)
admin.site.register(Skill)