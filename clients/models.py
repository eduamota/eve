# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.urls import reverse
from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone

class Phone_Number(models.Model):
	number = models.CharField(max_length=20)
	country = models.CharField(max_length=50)

	def __str__(self):              # __unicode__ on Python 2
		return self.number

class Language(models.Model):
	name = models.CharField(max_length=20)

	def __str__(self):              # __unicode__ on Python 2
		return self.name

class Payment_Model(models.Model):
	name = models.CharField(max_length=20)

	def __str__(self):              # __unicode__ on Python 2
		return self.name

class Client(models.Model):
	name = models.CharField(max_length=150)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('client-detail', kwargs={'pk': self.pk})

class Comment(models.Model):
	client = models.ForeignKey(Client, on_delete=models.CASCADE)
	comments = models.TextField(blank=True, null=True)
	change_time = models.DateTimeField(default=timezone.now, blank=True)
	change_by = models.ForeignKey(User, on_delete=models.CASCADE)

class Client_Info(models.Model):
	client = models.OneToOneField(Client)
	payments = models.IntegerField(blank=True, null=True)
	branded = models.BooleanField()
	hw_support_t1 = models.BooleanField()
	hw_support_t2 = models.BooleanField()
	support_language = models.ManyToManyField(Language, blank=True)
	domain = models.CharField(max_length=50, blank=True, null=True)
	payment_model = models.ManyToManyField(Payment_Model, blank=True)
	wallet_number = models.CharField(max_length=15, blank=True, null=True)
	custom_contact_info = models.BooleanField()
	phone_numbers = models.ManyToManyField(Phone_Number, blank=True)
	email_address = models.EmailField(blank=True, null=True)
	chat_float_window = models.CharField(max_length=50, blank=True, null=True)
	first_payment = models.DateField(blank=True, null=True)
	first_registration = models.DateField(blank=True, null=True)
	change_time = models.DateTimeField(default=timezone.now, blank=True)
	change_by = models.ForeignKey(User, on_delete=models.CASCADE)

	def __str__(self):              # __unicode__ on Python 2
		return self.name
