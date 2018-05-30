# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Quality_Form, Quality_Section, Quality_Question, Quality_Response

admin.site.register(Quality_Form)
admin.site.register(Quality_Section)
admin.site.register(Quality_Question)
admin.site.register(Quality_Response)
