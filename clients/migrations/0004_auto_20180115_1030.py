# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-15 18:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_client_additional_comments'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Client',
            new_name='Client_Info',
        ),
    ]
