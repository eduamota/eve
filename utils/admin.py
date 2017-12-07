# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Location, Profile, Skill, Skill_Level
# Register your models here.
admin.site.register(Location)
admin.site.register(Profile)
admin.site.register(Skill)
admin.site.register(Skill_Level)