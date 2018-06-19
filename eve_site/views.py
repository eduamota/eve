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

def home_page(request):


	return render(request, 'site/dashboard.html')

def agent_dashboard(request):
	req =	 requests.get("http://10.5.225.93/jasperserver/rest_v2/reports/Personal_Stats/Agent_Contact_Stats.html?Start_Date=2018-01-11&End_Date=2018-01-17&LoggedInUserEmailAddress=lgarcia@hyperwallet.com", auth=('emota','L!$e)&abby12'))
	js = req.text
	return render(request, 'site/agent_dashboard.html', {"stats":js})

def get_locations(request, timep = "current"):

	conn = mysql.connector.connect(host="10.5.225.93",	# your host, usually localhost
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
