# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from utils.models import Profile

# Create your models here.
class Form(models.Model):
    name = models.CharField(max_length=10)
    valid = models.BooleanField(default=False)

    def __str__(self):
       return self.name

class Section(models.Model):
    name = models.CharField(max_length=150)
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    order = models.DecimalField(max_digits=2, decimal_places=0)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name + " " + str(self.form)

class Question(models.Model):
    question = models.CharField(max_length=500)
    order = models.DecimalField(max_digits=2, decimal_places=0)
    section =  models.ForeignKey(Section, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.question + " " + str(self.section)

class Response(models.Model):
    answer = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    question = models.ManyToManyField(Question)

    def __str__(self):
        return self.answer + " " + str(self.weight)

class Form_Overview(models.Model):
    created_time = models.DateTimeField(auto_now_add=True, blank=False)
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.created_by.user.first_name + " " + self.created_by.user.last_name + " " + str(self.score)

class Form_Evaluation(models.Model):
    field = models.CharField(max_length=150)
    value = models.TextField()
    form_overview = models.ForeignKey(Form_Overview, on_delete=models.CASCADE)

    def __str__(str):
        return self.field

class Evaluation(models.Model):
    field = models.CharField(max_length=150)
    value = models.TextField(max_length=150)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    form_overview = models.ForeignKey(Form_Overview, on_delete=models.CASCADE)

    def __str__(self):
        return self.field + " " + self.question + " " + self.value
