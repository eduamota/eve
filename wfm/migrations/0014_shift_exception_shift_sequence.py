# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-16 13:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wfm', '0013_job_parameters'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift_exception',
            name='shift_sequence',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='wfm.Shift_Sequence'),
            preserve_default=False,
        ),
    ]
