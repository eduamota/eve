# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-16 04:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_auto_20180115_1049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client_info',
            name='domain',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='client_info',
            name='support_language',
            field=models.ManyToManyField(blank=True, null=True, to='clients.Language'),
        ),
    ]
