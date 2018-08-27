# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 04:26:54 2018

@author: emota
"""
from __future__ import unicode_literals

from quality.models import *
from django.contrib.auth.models import User
from datetime import timedelta, datetime, date
from django.db import connection
import pytz
import sys
import json
from background_task import background
from django.db.models import Q
import os
import csv

#@background(schedule=1)
def generateCSV(timezone, start_time, end_time):
    '''
    Generates the csv files containing all the fields of the form

    @parameters

    timezone - Timezone of the user
    start_time - Date time from where to start the pull of data
    end_time - Date of the until where to end the pull of data

    save data in a temporary file
    '''
    tz = pytz.timezone(timezone)

    start_t = start_time
    end_t = end_time

    start_format = start_t.strftime("%Y-%m-%d %H:%M:%S")
    end_format = end_t.strftime("%Y-%m-%d %H:%M:%S")

    query = "SELECT qfo.id, au.first_name, au.last_name, CONVERT_TZ(qfo.created_time, 'UTC', '{}'), qfo.score, qq.question, qe.value, qq.weight FROM quality_form_overview qfo INNER JOIN utils_profile up on qfo.created_by_id = up.id INNER JOIN auth_user au on up.user_id = au.id INNER JOIN quality_evaluation qe on qe.form_overview_id = qfo.id INNER JOIN quality_question qq on qq.id = qe.question_id WHERE qfo.created_time between '{}' and '{}' ORDER BY qfo.id, qq.section_id, qq.`order`".format(timezone, start_format, end_format)

    with connection.cursor() as cur:
        cur.execute(query)
        overviews = cur.fetchall()

    start_format = start_t.strftime("%Y%m%d%H%M%S")
    end_format = end_t.strftime("%Y%m%d%H%M%S")

    file_name = os.path.join(os.path.realpath(""), "eve_site")
    file_name = os.path.join(file_name, "tmp")
    file_name = os.path.join(file_name, "quality{}.csv".format(start_format+end_format,))

    print(file_name)

    with open(file_name, 'wb') as f:
    	writer = csv.writer(f)
    	writer.writerow(["form_id", "agent_first_name", "agent_last_name", "evaluation_date", "score", "question", "value", "weight"])
    	writer.writerows(overviews)

    filename = __file__ # Select your file here.
    wrapper = FileWrapper(file(filename))
    response = HttpResponse(wrapper, content_type='text/plain')
    response['Content-Length'] = os.path.getsize(filename)
    return response
