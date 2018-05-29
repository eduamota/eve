# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from utils.models import Profile

# Create your models here.
class Quality_Form(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
       return self.name

class Quality_Section(models.Model):
    name = models.CharField(max_length=150)
    form = models.ForeignKey(Quality_Form, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name

class Quality_Question(models.Model):
    question = models.CharField(max_length=500)
    section =  models.ForeignKey(Quality_Section, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.question

class Quality_Responses(models.Model):
    answer = models.CharField(max_length=5)
    question = models.ForeignKey(Quality_Question, on_delete=models.CASCADE)

    def __str__(self):
        return answer
