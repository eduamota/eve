# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-16 22:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client_info',
            name='additional_comments',
        ),
    ]
