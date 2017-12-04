# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from wfm.models import *
from django.contrib.auth.models import User, Group
from datetime import timedelta, datetime, date
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .tasks import runsaveShift, runsaveBreaks, runsaveShiftBreaks, runsaveMeetings
from django.db import connection
from django.db.models import Q
import pytz
from datetime import datetime
import json

def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
	return next_month - timedelta(days=next_month.day)

@login_required
def add_jobs(request):
	if 'action' in request.POST and request.POST['action']:
		j = Job(job_type = request.POST['action'],
			from_date = request.POST['from'],
			to_date = request.POST['to'],
			agents = str(request.POST['agent']), 
			actioned_by = request.user)
	#print j
	
	return render(request, 'wfm/add_job.html')
			
	
def scheduler(request, action = False):
	messages = {}
	response = {}

	if action:			
		actions = "Scheduler"
		start_date = '1990-01-01'
		end_date = '1990-01-02'
		agent = 0
		
		start_date = datetime.strptime(start_date, '%Y-%m-%d')
		end_date = datetime.strptime(end_date, '%Y-%m-%d')
		
		start_date = start_date.astimezone('UTC')
		end_date = end_date.astimezone('UTC')
		
		st = Job_Status.objects.get(name="Running")
		
		j = Job.objects.filter(status = st, job_type = "Scheduler")
		#runScheduler()
		if len(j) == 0 and action == "run":
		#if action == "run":
			j = Job(job_type = actions,
				from_date = start_date,
				to_date = end_date,
				agents = agent,
				status = st,
				actioned_by = request.user)
		
			j.save()
			
			response = {"status":"success", "job status": j.status.name}
		elif len(j) > 0 and action == "stop":
			st = Job_Status.objects.get(name="Success")
			jo = j[0]
			jo.status = st
			jo.save()
			response = {"status":"success", "job status": jo.status.name}
		elif len(j) == 1:
			response = {"status":"error", "message":"already running"}
		else:
			response = {"status":"error", "message":"scheduler not runnig"}
			
		messages['The job ' + action + ' has been saved'] = "green"
	return JsonResponse(response, safe=False)
	
@login_required
def schedule_job(request):
	agents = User.objects.filter(groups__name = 'Agent')
	agent_list = {0:"All"}

	tz = pytz.timezone(request.user.profile.location.iso_name)
	
	messages = {}
	for a in agents:
		agent_list[a.pk] = a.first_name + " " + a.last_name
		
	event_list = {"Add_Breaks_and_Lunches":"Add Breaks and Lunches",
			"Optimize_Breaks_and_Lunches":"Optimize Breaks and Lunches",
			"Schedule_a_Meeting":"Schedule a Meeting", 
			"Insert_Shifts":"Insert Shifts",
			"Insert_Shifts_&_Breaks":"Insert Shifts and add Breaks"}
			
	if 'action' in request.POST:
		#print(request.POST)
		actions = request.POST.getlist('action')
		start_date = request.POST.getlist('from')
		end_date = request.POST.getlist('to')
		agent = request.POST.getlist('agent')
		
		start_date = datetime.strptime(start_date[0], '%d %B, %Y')
		start_date = tz.localize(start_date)
		
		end_date = datetime.strptime(end_date[0], '%d %B, %Y')
		end_date = tz.localize(end_date)
		
		st = Job_Status.objects.get(name="Queued")
		
		param = ""
		
		if actions[0] == "Schedule_a_Meeting":
			group_size = request.POST['group_size']
			notes = request.POST['meeting_notes']
			event = request.POST['event']
			override = ""
			duration = request.POST['duration']
			if "override" in request.POST:
				override = request.POST['override']
			
			param = {"group_size": group_size, "override" : override, "notes": notes, "event": event, "duration":duration}
		
		for a in agent:
			j = Job(job_type = actions[0],
				from_date = start_date,
				to_date = end_date,
				agents = a,
				status = st,
				actioned_by = request.user,
				parameters = json.dumps(param))
			
			j.save()
		messages['The job ' + request.POST['action'] + ' has been saved'] = "green"
		
		if actions[0] == 'Insert_Shifts':
			runsaveShift.delay()
		elif actions[0] == 'Add_Breaks_and_Lunches':
			runsaveBreaks.delay()
		elif actions[0] == 'Insert_Shifts_&_Breaks':
			runsaveShiftBreaks.delay()
		elif actions[0] == 'Schedule_a_Meeting':
			runsaveMeetings.delay()
	
	return render(request, 'wfm/add_exceptions.html', {'agent_list': agent_list, 'event_list': event_list, "messages": messages})
	


def set_timezone(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('/')
    else:
        return render(request, 'wfm/tz.html', {'timezones': pytz.common_timezones})	

# Create your views here.
@login_required
def calendar(request):	
	actions = {"timeoff":"Request Time Off",
			"overtime":"Request Overtime",
			"meeting":"Request a 1-1 / Coaching",
								}
	return render(request, 'wfm/default.html', {"actions":actions,})
	
@login_required
def calendar_team(request):	
	return render(request, 'wfm/calendar_team.html')
	
def events(request, sDate = False, eDate = False):
	schedule = getShifts(request)
	return JsonResponse(schedule, safe=False)
	
def team_events(request, sDate = False, eDate = False):
	schedule = getTeamShifts(request)
	return JsonResponse(schedule, safe=False)

	
def getShifts(request):
	current_user = request.user
	user = User.objects.get(username = current_user.username)
	profile = Profile.objects.get(user = user)
	
	tzo = pytz.timezone(request.user.profile.location.iso_name)
	
	start = datetime.now(tzo)
	end = last_day_of_month(datetime.now(tzo))
	
	if 'start' in request.GET and request.GET['start']:
		start = request.GET['start']
		if len(start) < 16:
			start += "T00:00:00"
		start = tzo.localize(datetime.strptime(start, '%Y-%m-%dT%H:%M:%S'))
		
		
	if 'end' in request.GET and request.GET['end']:
		end = request.GET['end']
		if len(end) < 16:
			end+= "T00:00:00"
		end = tzo.localize(datetime.strptime(end, '%Y-%m-%dT%H:%M:%S'))

	exceptions = Shift_Exception.objects.filter(user=profile)
	exceptions = exceptions.filter(approved=True)
	exceptions = exceptions.filter(start_date_time__gte=start)
	exceptions = exceptions.filter(end_date_time__lt=end)

	schedule = []
	events = {}

	for e in exceptions:
		date_e = e.start_date_time.astimezone(tzo).strftime("%Y-%m-%d")
		ev = {"title": e.event.name, "start":e.start_date_time.astimezone(tzo).strftime("%Y-%m-%d %H:%M:%S"), "end":e.end_date_time.astimezone(tzo).strftime("%Y-%m-%d %H:%M:%S"), "color":e.event.color, "textColor":e.event.text_color, "id":e.pk}

		if not(events.has_key(date_e)):
			events[date_e] = []
		events[date_e].append(ev)
	
	while start < end:
		start_query = start
		start_format = start.astimezone(tzo).strftime("%Y-%m-%d")
		end_query = start_query + timedelta(days=1)
		
		if start_format in events:
			for e in events[start_format]:
				schedule.append(e)
		
		sh_f = Shift_Sequence.objects.filter(Q(user= profile), Q(start_date_time__range = (start_query, end_query)) |  Q(end_date_time__range = (start_query, end_query)) )	
		
		for sh1 in sh_f:
			start_d = sh1.start_date_time.astimezone(tzo)
			end_d = sh1.end_date_time.astimezone(tzo)

			if start_d < start:
				start_d = start
			if end_d > (start + timedelta(days=1)):
				end_d = (start + timedelta(days=1))
			
			schedule.append({"start": start_d.strftime("%Y-%m-%d %H:%M:%S"), "end": end_d.strftime("%Y-%m-%d %H:%M:%S"), "title":"Shift"})
			
		start = start + timedelta(days=1)
	
	return schedule
	
def getResources(request):
	all_users = User.objects.filter(groups__name = 'Agent')
	schedule = []
	resource_cc = {}
	resource_cc['id'] = "CC"
	resource_cc['title'] = "Contact Center"
	schedule.append(resource_cc)
	
	for us in all_users:
		
		resource_cc = {}
		resource_cc['id'] = str(us.pk)
		resource_cc['title'] = us.first_name + " " + us.last_name
		resource_cc['parentId'] = "CC"
		
		schedule.append(resource_cc)
		
	return JsonResponse(schedule, safe=False)
	
def getTeamShifts(request):
	all_users = User.objects.filter(groups__name = 'Agent')
	
	schedule = []

	tz = pytz.timezone(request.user.profile.location.iso_name)	
	
	for us in all_users:
		
		profile = Profile.objects.get(user = us)
		start = date.today()
		end = last_day_of_month(date.today())
		
		if 'start' in request.GET and request.GET['start']:
			start = request.GET['start'][:10]
			start = tz.localize(datetime.strptime(start, '%Y-%m-%d'))
			
			
		if 'end' in request.GET and request.GET['end']:
			end = request.GET['end'][:10]
			end = tz.localize(datetime.strptime(end, '%Y-%m-%d'))
	
		exceptions = Shift_Exception.objects.filter(user=profile)
		exceptions = exceptions.filter(approved=True)
		exceptions = exceptions.filter(start_date_time__gte=start)
		exceptions = exceptions.filter(end_date_time__lte=end)
	
		events = {}
	
		for e in exceptions:
			date_e = e.start_date_time.astimezone(tz).strftime("%Y-%m-%d")
			ev = {"title": e.event.name, "start":e.start_date_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), "end":e.end_date_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), "color":e.event.color, "textColor":e.event.text_color, "id":e.pk, "resourceId": str(us.pk)}
	
			if not(events.has_key(date_e)):
				events[date_e] = []
			events[date_e].append(ev)
		
		while start < end:
			start_query = start
			start_format = start.strftime("%Y-%m-%d")
			end_query = start_query + timedelta(days=1)
			end_query = end_query
			
			if start_format in events:
				for e in events[start_format]:
					schedule.append(e)
			
			sh_f = Shift_Sequence.objects.filter(Q(user= profile), Q(start_date_time__range = (start_query, end_query)) |  Q(end_date_time__range = (start_query, end_query)) )	
			for sh1 in sh_f:
				start_d = sh1.start_date_time.astimezone(tz)
				end_d = sh1.end_date_time.astimezone(tz)
	
				if start_d.date() < start.date():
					start_d = start.replace(hour=0, minute=0)
				if end_d.date() > start.date():
					end_d = end_d.replace(hour=0, minute=0)
				
				schedule.append({"start": start_d.strftime("%Y-%m-%d %H:%M:%S"), "end": end_d.strftime("%Y-%m-%d %H:%M:%S"), "title":"Shift", "id":sh1.pk, "resourceId": str(us.pk)})
				
			start = start + timedelta(days=1)
		
		
	
	return schedule
	
def addAgent(request):
	c = connection.cursor()
	
	if request.POST:
		employees = request.POST.getlist('agent')
		
		for employee_id in employees:
			
			location = request.POST['location']
			
			password = request.POST['pwd']
			groups = request.POST.getlist('group')
			
			
			c.execute("SELECT * FROM ops_system.otrs_user where id = %s", (employee_id,))
	
			agent_info = c.fetchone()
			
			username = agent_info[1]
			first_name = agent_info[3]
			last_name = agent_info[4]
			email = agent_info[5]
			
			
			c.execute("SELECT * FROM ops_system.voxter_user where email = %s and valid = 1", (email,))
	
			agent_ext = c.fetchone()
			
			extension = agent_ext[5]
			
			
			new_agent = User.objects.create_user(username, email, password)
			new_agent.first_name = first_name
			new_agent.last_name = last_name
			new_agent.groups = groups
			
			new_agent.profile.employee_number = employee_id
			
			Loc = Location.objects.get(pk=location)
			new_agent.profile.location = Loc
			
			new_agent.profile.extension = extension
			
			if "label" in request.POST:
				labels = request.POST['label']
				new_agent.profile.label = labels
			
			if "skills" in request.POST and len(request.POST.getlist('skill')) > 0:
				skills = request.POST.getlist('skill')
				new_agent.profile.skill = skills
			
			
			new_agent.save()
		
	agents = User.objects.filter(Q(groups__name = 'Agent') | Q(groups__name = 'Supervisor') | Q(groups__name = 'TeamLead'))
	groups = Group.objects.all()	
	
	agent_list = []
	for a in agents:
		agent_list.append(a.profile.employee_number)
	agents = {}
	
	group_list = {}
	for g in groups:
		group_list[g.id] = g.name
		
	
	
	c.execute("SELECT ID, CONCAT(First_Name, ' ', Last_Name) as AgentName FROM ops_system.otrs_user where title like '%Customer Service%' AND OTRS_ENABLE = 1")

	results = c.fetchall()

	for r in results:
		if r[0] in agent_list:
			continue
		else:
			agents[r[0]] = r[1]
	
	
	
	sks = Skill.objects.all()
	lo = Location.objects.all()
	
		
	c.close()
	return render(request, "wfm/add_user.html", {'agent_list':agents, 'skills':sks, 'locations': lo, 'groups': group_list})