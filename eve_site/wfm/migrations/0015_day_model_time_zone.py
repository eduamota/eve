# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-17 20:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wfm', '0014_shift_exception_shift_sequence'),
    ]

    operations = [
        migrations.AddField(
            model_name='day_model',
            name='time_zone',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
