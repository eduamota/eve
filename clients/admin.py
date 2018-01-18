# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Client, Client_Info, Language, Phone_Number, Payment_Model

admin.site.register(Client)
admin.site.register(Client_Info)
admin.site.register(Language)
admin.site.register(Phone_Number)
admin.site.register(Payment_Model)