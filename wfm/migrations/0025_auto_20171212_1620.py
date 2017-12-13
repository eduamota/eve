# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-13 00:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0006_auto_20171212_1607'),
        ('wfm', '0024_auto_20171212_1607'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='profile',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='utils.Profile'),
        ),
        migrations.AddField(
            model_name='log',
            name='shift_sequence',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='wfm.Shift_Sequence'),
        ),
    ]
