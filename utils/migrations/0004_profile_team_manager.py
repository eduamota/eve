# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-05 01:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('utils', '0003_auto_20171204_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='team_manager',
            field=models.ForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.CASCADE, related_name='team_manager', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
