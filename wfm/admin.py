# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Shift, Day_Model, Event_Group, Event, Shift_Exception, Shift_Sequence


class Shift_Admin(admin.ModelAdmin):
    list_display = ['user', 'day_model', 'valid_from', 'valid_to', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    ordering = ['user', 'valid_from']
    search_fields = ['user__user__first_name', 'user__user__last_name', 'valid_from', 'day_model']

admin.site.register(Shift, Shift_Admin)
admin.site.register(Day_Model)
admin.site.register(Event_Group)
admin.site.register(Event)

class Shift_ExceptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'start_date_time', 'end_date_time', 'approved']
    ordering = ['user', 'start_date_time']
    search_fields = ['user__user__first_name', 'user__user__last_name', 'start_date_time', 'end_date_time', 'approved']

admin.site.register(Shift_Exception, Shift_ExceptionAdmin)

class Shift_SequenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'start_date_time', 'end_date_time']
    ordering = ['user', 'start_date_time']
    search_fields = ['user__user__first_name', 'user__user__last_name', 'start_date_time', 'end_date_time']

admin.site.register(Shift_Sequence, Shift_SequenceAdmin)
