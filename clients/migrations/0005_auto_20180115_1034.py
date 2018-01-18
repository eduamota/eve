# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-15 18:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_auto_20180115_1030'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
            ],
        ),
        migrations.RemoveField(
            model_name='client_info',
            name='name',
        ),
        migrations.AddField(
            model_name='client_info',
            name='client',
            field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, to='clients.Client'),
            preserve_default=False,
        ),
    ]
