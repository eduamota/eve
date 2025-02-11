# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-04 23:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Skill_Level',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.DecimalField(decimal_places=0, max_digits=3)),
            ],
        ),
        migrations.RemoveField(
            model_name='skill',
            name='level',
        ),
        migrations.AddField(
            model_name='skill_level',
            name='skill',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='utils.Skill'),
        ),
        migrations.AddField(
            model_name='skill_level',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='utils.Profile'),
        ),
    ]
