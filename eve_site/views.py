# -*- coding: utf-8 -*-
"""
Created on Fri Nov 03 12:52:03 2017

@author: emota
"""

from __future__ import unicode_literals
import requests
from django.shortcuts import render
import mysql.connector
import pandas as pd
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.db import connection
import datetime
from django.contrib.auth.models import User, Group
import json
try:
	from urllib.parse import urlencode
	from urllib.request import urlopen, Request
except ImportError: # Python 2
	from urllib import urlencode
	from urllib2 import urlopen, Request

roles = {"supervisor": False, "agent": False, "clientadmin": False, "teamlead": False, "wfmadmin": False, "qa": False}
request_actions = {"/wfm/request/Timeoff":"Request Time Off",
			"/wfm/request/Overtime":"Request Overtime",
			"/wfm/request/Meeting":"Request a 1-1 / Coaching",
								}

# Create your views here.
class MethodRequest(Request):
	def __init__(self, *args, **kwargs):
		self._method = kwargs.pop('method', None)
		Request.__init__(self, *args, **kwargs)

	def get_method(self):
		return self._method if self._method else super(RequestWithMethod, self).get_method()

from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False

def callAPI(met, url, data = False):

	c = connection.cursor()

	c.execute("SELECT account_id, value_text from ops_system.crd where System = 'Voxter'")
	authToken = c.fetchone()
	account_id = authToken[0]
	authToken = authToken[1]

	url = url.replace("{accountID}", account_id)

	req = MethodRequest(url, method=met)
	req.add_header('Content-Type', 'application/json')
	req.add_header('X-Auth-Token', authToken)
	r = {}
	if met == "POST" and data:
		dataDic = {'data':data, "verb":"POST"}
		r = urlopen(req, json.dumps(dataDic))
	else:
		r = urlopen(req)
	c.close()
	return json.loads(str(r.read()))

@login_required()
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('home_page')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form
    })

@login_required()
def home_page(request):
    for r, v in roles.items():
        roles[r] = False
    group = request.user.groups.values_list('name', flat=True)
    for g in group:
        #print(str(g).lower())
        if str(g).lower() == 'admin':
            for r, v in roles.items():
                roles[r] = True
            break
        if str(g).lower() in roles:
            roles[str(g).lower()] = True
    #print(roles)
    return render(request, 'site/dashboard.html', {"roles": roles,})

@login_required()
def agent_dashboard(request):
	name = request.user.first_name + " " + request.user.last_name
	return render(request, 'site/agent_dashboard.html', {"agentName":name, "actions": request_actions})

@login_required()
def test_agent_dashboard(request):
	name = request.user.first_name + " " + request.user.last_name
	return render(request, 'site/test_dashboard.html', {"agentName":name, "actions": request_actions})

def get_locations(request, timep = "current"):

	conn = mysql.connector.connect(host="localhost",	# your host, usually localhost
					 user='emota',		 # your username
					 passwd='L!$e)&abby12',  # your password
					 db="ops_system")		# name of the data base

	query = "Select replace(caller_id_number, '-', '') as caller_id_number from `call` where status = 'waiting' union all select replace(caller_id_num, '-', '') as caller_id_number from `agent_status` where duration is null and `state` = 'connected' and start_time >= DATE_SUB(NOW(),INTERVAL 2 HOUR) and caller_id_num != 'Unavailable'"
	#print(timep)
	if timep == "day":
		query = "Select replace(caller_id_number, '-', '') as caller_id_number from `call` where status = 'waiting' union all select replace(caller_id_num, '-', '') as caller_id_number from `agent_status` where `state` = 'connected' and start_time >= DATE_SUB(NOW(),INTERVAL 24 HOUR) and caller_id_num != 'Unavailable'"
	#print(query)
	call_dataset = pd.read_sql_query(query, conn)

	query = "Select `province-state`, `area code`, country, lat, lng from numbering_plan_north_america union all select Null, `phone code`, `country name`, lat, lng from numbering_plan_global where `phone code` != 1"

	na_dataset = pd.read_sql_query(query, conn)

	conn.close()

	call_dataset.describe()



	call_dataset['na'] = call_dataset['caller_id_number'].apply(lambda x: ('1'+str(x.replace('+','')[:3]))).astype('int64')
	call_dataset['na2'] = call_dataset['caller_id_number'].apply(lambda x: x[:4]).astype('int64')
	call_dataset['int'] = call_dataset['caller_id_number'].apply(lambda x: x[:2]).astype('int64')
	call_dataset['int3'] = call_dataset['caller_id_number'].apply(lambda x: x[:3]).astype('int64')



	final = call_dataset.merge(na_dataset, left_on='na', right_on='area code', how='left')
	final2 = call_dataset.merge(na_dataset, left_on='int', right_on='area code', how='left')
	final3 = call_dataset.merge(na_dataset, left_on='int3', right_on='area code', how='left')
	final4 = call_dataset.merge(na_dataset, left_on='na2', right_on='area code', how='left')

	combined = pd.concat([final.dropna(subset=['country'], how='all'), final2.dropna(subset=['country'], how='all'), final3.dropna(subset=['country'], how='all'), final4.dropna(subset=['country'], how='all')])

	locations = {}

	for index, row in combined.iterrows():

		if row['province-state'] and (len(row['caller_id_number']) == 10 or row['caller_id_number'][:1] ==1):
			locations[row['caller_id_number']] = row['province-state']
		elif row['caller_id_number'] not in locations and row['province-state'] == None:
			locations[row['caller_id_number']] = row['country']

	loc = pd.DataFrame(locations.items(), columns=['num', 'country'])

	loc_agg = loc.groupby(['country']).count()

	loca_lng_lat = loc_agg.merge(na_dataset, left_index=True, right_on='province-state', how='left')
	loca_lng_lat2 = loc_agg.merge(na_dataset, left_index=True, right_on='country', how='left')

	loca_lng_lat['Name'] = loca_lng_lat['province-state'] + ", " + loca_lng_lat['country'] + ", " + loca_lng_lat['num'].astype('str')
	loca_lng_lat2['Name'] = loca_lng_lat2['country'] + ", " + loca_lng_lat2['num'].astype('str')

	loc_lng_lat = pd.concat([loca_lng_lat.dropna(subset=['lat', 'lng'], how='all'), loca_lng_lat2.dropna(subset=['lat', 'lng'], how='all')])


	total = loc_lng_lat['num'].max()

	if total < 20:
		total = 20

	loc_lng_lat['freq'] = (loc_lng_lat['num']*40)/total

	loc_lng_lat['fr'] = loc_lng_lat['freq'].apply(lambda x: 15.0 if x < 5 else (20.0 if x < 10 else x) )

	response = {
			"lat": loc_lng_lat['lat'].tolist(),
			"lng": loc_lng_lat['lng'].tolist(),
			"name": loc_lng_lat['Name'].tolist(),
			'freq': loc_lng_lat['fr'].tolist(),
			'color': [90]*len(loc_lng_lat['lat'])
		}

	return JsonResponse(response)

def globe_dashboard(request, timep = "current"):

	if timep == "day":
		return render(request, 'site/daily_map.html')
	else:
		return render(request, 'site/big_dashboard.html')

def tm_dashboard(request):
	return render(request, 'site/tm_dashboard.html')

def getAgentStats(request):
	#with connection.cursor() as c:
	#	c.execute("SELECT ")
    test_user = User.objects.get(pk=49)
    print(test_user)
    email = test_user.email
    employee_id = test_user.profile.employee_number
    response = {'calls':0, 'aht': "0:00", 'awt': "0:00", 'chats':0, "act": "0:00", "emails": 0}
    query = "select v.Agent_ID from ops_system.voxter_user v where v.email = '{}'".format(email,)
    query2 = "select state, a.Pause_Event, avg(duration), count(duration) from ops_system.agent_status a where a.agent_id = '{}' and a.Start_Time >= date(NOW()) group by state, a.Pause_Event"
    query3 = "select count(id), avg(chat_time) from ops_etl.chat_info where agent_id = {} and created_datetime >= date(NOW()) and chat_time > 0".format(employee_id,)
    data = None

    with connection.cursor() as c:
        c.execute(query)
        agent_id = c.fetchall()
        c.execute(query2.format(agent_id[0][0]))
        data = c.fetchall()
        c.execute(query3)
        c_data = c.fetchall()

    if data:
        response = {}
        for row in data:
            if row[0] == 'connected':
                response['calls'] = row[3]
                response['aht'] = str(datetime.timedelta(seconds=int(row[2])))
            elif row[1] == 'Wrapup time':
                response['awt'] = str(datetime.timedelta(seconds=int(row[2])))

    response['chats'] = c_data[0][0]
    if c_data[0][1]:
    	response['act'] = str(datetime.timedelta(seconds=int(c_data[0][1])))
    return JsonResponse(response)

def getAgentContacts(request):

    email = request.user.email

    query = "select v.Agent_ID from ops_system.voxter_user v where v.email = '{}'".format(email,)
    query2 = "select state, caller_id, duration, a.Pause_Event, a.Start_Time from ops_system.agent_status a where a.agent_id = '{}' and a.Start_Time >= date(NOW()) and state != 'Wrapup' order by id desc"
    data = None

    response = [{"callerid": "Loading...", "duration": "Loading...", "state": "Loading..."},]

    with connection.cursor() as c:
        c.execute(query)
        agent_id = c.fetchall()
        c.execute(query2.format(agent_id[0][0]))
        data = c.fetchall()

    if data:
        response = []
        for row in data:
            tmp = {}
            tmp['state'] = row[0].capitalize()
            if row[3]:
                tmp['state'] = tmp['state'] + " " + row[3]
            tmp['callerid'] = row[1]
            dur = None
            if row[2]:
                dur = str(datetime.timedelta(seconds=row[2]))
            else:
                dur = (datetime.datetime.now() - row[4]).total_seconds()
                dur = str(datetime.timedelta(seconds=int(dur)))
            tmp['duration'] = dur
            response.append(tmp)

    return JsonResponse(response, safe=False)

def change_agent_state(request, state="resume"):

    status = state

    email = request.user.email

    query = "select v.Agent_ID from ops_system.voxter_user v where v.email = '{}'".format(email,)
    agent_id = None

    messages = {"status:": "Failed"}

    with connection.cursor() as c:
        c.execute(query)
        agent_id = c.fetchall()

    agentid = agent_id[0][0]

    url = "https://api-hw.voxter.com:8443/v1/accounts/{accountID}/agents/" + agentid + "/status"

    if "login" in status or "logout" in status or "resume" in status:
        data = {"status": status}
    else:
        data = {"status":"pause", "alias": status}
    results = callAPI("POST", url, data)

    if results['status'] == "success":
        messages = {"status": "Success status changed to " + status}
    else:
        messages = {"status": "Error unable to set status to " + status}


    return JsonResponse(messages, safe=False)
