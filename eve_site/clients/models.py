# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone

class Phone_Number(models.Model):
	number = models.CharField(max_length=20)
	country = models.CharField(max_length=50)
	
class Language(models.Model):
	name = models.CharField(max_length=20)
	
class Payment_Model(models.Model):
	name = models.CharField(max_length=20)

class Client(models.Model):	
	name = models.CharField(max_length=50)
	payments = models.IntegerField(blank=True)
	branded = models.BooleanField()
	hw_support_t1 = models.BooleanField()
	hw_support_t2 = models.BooleanField()
	support_language = models.ManyToManyField(Language)
	domain = models.CharField(max_length=50)
	payment_model = models.ManyToManyField(Payment_Model, blank=True)
	wallet_number = models.CharField(max_length=15, blank=True)
	custom_contact_info = models.BooleanField()
	phone_numbers = models.ManyToManyField(Phone_Number, blank=True)
	email_address = models.EmailField(blank=True)
	chat_float_window = models.CharField(max_length=50, blank=True)
	additional_comments = models.TextField(blank=True)
	change_time = models.DateTimeField(default=timezone.now)
	change_by = models.ForeignKey(User, on_delete=models.CASCADE)
	