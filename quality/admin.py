# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Form, Section, Question, Response

admin.site.register(Form)
admin.site.register(Section)
admin.site.register(Question)
admin.site.register(Response)
