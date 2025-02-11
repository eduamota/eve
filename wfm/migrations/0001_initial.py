# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-11 23:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Day_Model',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('valid_from', models.DateField(default='2017-01-01')),
                ('valid_to', models.DateField(default='2017-12-31')),
                ('day_start_time', models.TimeField(default='06:00:00')),
                ('day_start_diff', models.DecimalField(decimal_places=0, default=0, max_digits=1)),
                ('day_end_time', models.TimeField(default='14:30:00')),
                ('day_end_diff', models.DecimalField(decimal_places=0, default=0, max_digits=1)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('color', models.CharField(max_length=7)),
                ('text_color', models.CharField(max_length=7)),
                ('paid', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Event_Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('iso_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_number', models.SmallIntegerField()),
                ('extension', models.SmallIntegerField()),
                ('label', models.CharField(max_length=150)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wfm.Location')),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valid_from', models.DateField(default='2017-01-01')),
                ('valid_to', models.DateField(default='2017-12-31')),
                ('sunday', models.BooleanField(default=False)),
                ('monday', models.BooleanField(default=False)),
                ('tuesday', models.BooleanField(default=False)),
                ('wednesday', models.BooleanField(default=False)),
                ('thursday', models.BooleanField(default=False)),
                ('friday', models.BooleanField(default=False)),
                ('saturday', models.BooleanField(default=False)),
                ('day_model', models.ManyToManyField(to='wfm.Day_Model')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='wfm.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='Shift_Exception',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date_time', models.DateTimeField()),
                ('start_diff', models.DecimalField(decimal_places=0, max_digits=1)),
                ('end_date_time', models.DateTimeField()),
                ('end_diff', models.DecimalField(decimal_places=0, max_digits=1)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wfm.Event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wfm.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('level', models.DecimalField(decimal_places=0, max_digits=3)),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='skill',
            field=models.ManyToManyField(to='wfm.Skill'),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wfm.Event_Group'),
        ),
    ]
