# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from reports.models import *
from django.contrib.auth.models import User, Group
from datetime import timedelta, datetime, date
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q
import pytz
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
import sys, os

# Create your views here.

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'Supervisor']).exists())
def gap_analysis(request):

    return render(request, 'reports/gap_analysis.html')

def get_heatmap_data(request):

    iso_name = request.user.profile.location.iso_name
    tzo = pytz.timezone(iso_name)

    start = None
    end = None

    if 'start' in request.GET and request.GET['start']:
        start = request.GET['start']
        if len(start) < 16:
            start += "T00:00:00"
        start = tzo.localize(datetime.strptime(start, '%Y-%m-%dT%H:%M:%S'))

    start_time = start.astimezone(pytz.utc)
    start_time_format = start_time.strftime('%Y-%m-%d %H:%M:%S')

    if 'end' in request.GET and request.GET['end']:
        end = request.GET['end']
        if len(end) < 16:
            end+= "T00:00:00"
        end = tzo.localize(datetime.strptime(end, '%Y-%m-%dT%H:%M:%S'))

    end_time = end.astimezone(pytz.utc)
    end_time_format = end_time.strftime('%Y-%m-%d %H:%M:%S')

    query = "SELECT convert_tz(`date`, 'UTC', '{}'), sum(calls_offered), sum(agents_required), sum(actual_agents_scheduled) from forecast_call_forecast where `date` between '{}' and '{}' and queue in ('English', 'Spanish') group by `date`".format(iso_name, start_time_format, end_time_format)

    print(query)

    timesheet = None

    schedule = []

    with connection.cursor() as cur:
        cur.execute(query)
        timesheet = cur.fetchall()

    for row in timesheet:
        start_time = row[0]
        end_time = start_time + timedelta(minutes = 15)

        calls_offered = row[1]
        agents_required = row[2]
        agents_scheduled = row[3]

        if calls_offered == 0:
            agents_required = 0

        if row[0].hour >= 8 and row[0].hour < 5:
            agents_scheduled = agents_scheduled - 3
        else:
            agents_scheduled = agents_scheduled - 1

        title = "co {} - ar {} - as {}".format(calls_offered, agents_required, agents_scheduled)

        color = "#008288"

        if float(agents_scheduled) - float(agents_required) < 0 and agents_required > 0:
            color = "#FF0000"
        elif float(agents_scheduled) - float(agents_required) == 0 and agents_required > 0:
            color = '#ff5733'

        schedule.append({"start": start_time.strftime("%Y-%m-%d %H:%M:%S"), "end": end_time.strftime("%Y-%m-%d %H:%M:%S"), "title":title, "color":color, "textColor":"#fff"})

    return JsonResponse(schedule, safe=False)
