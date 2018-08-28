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

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'Agent']).exists())
def gap_analysis(request):

	return render(request, 'reports/gap_analysis.html')

def get_heatmap_data(request):

    query = ("SELECT `date`, sum(calls_offered), sum(agents_required), sum(actual_agents_scheduled) from forecast_call_forecast where `date` between '2018-08-01' and '2018-08-31' and calls_offered > 0")

    timesheet = None

    schedule = []

    with connection.close() as cursor:
        cur.execute(query)
        tiemsheet = cur.fetchall()

    for row in timesheet:
        start_time = row[0]
        end_time = start_time + timedelta(minutes = 15)
        title = "{} - {} - {}".format(row[1], row[2], row[3])

        schedule.append({"start": start_time.strftime("%Y-%m-%d %H:%M:%S"), "end": end_time.strftime("%Y-%m-%d %H:%M:%S"), "title":title, "color":"#008288", "textColor":"#fff"})

    return JsonResponse(schedule, safe=False)
