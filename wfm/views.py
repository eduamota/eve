# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from wfm.models import *
from django.contrib.auth.models import User, Group
from datetime import timedelta, datetime, date
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q
import pytz
from .tasks import runsaveShift, runsaveBreaks, runsaveShiftBreaks, runsaveMeetings
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
import sys, os

# Define the actions that show up at the context menu
request_actions = {"../request/Timeoff":"Request Time Off",
			"../request/Overtime":"Request Overtime",
			"../request/Meeting":"Request a 1-1 / Coaching",
								}
# Helper fucntion to get the last of the month. Helps with date ranges
def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
	return next_month - timedelta(days=next_month.day)

# Adding shifts, optimizing breaks, and meetings are consider jobs. Use test to limit who can run this function
@user_passes_test(lambda u: u.groups.filter(name__in=['Admin',]).exists())
def schedule_job(request):
	''' Saves into a database a job to add shifts, optime breaks, or schedule meetings.

	@PARAMS:
		request: Standard request oject from django

	@RETURNS:
		request: As required by the Django rest_framework
		HTML: The wfm/add_exceptions.html renders the job to be added, the time frame, and the users that need to be consider for the job
		agent_list: List of all agents ordered by first name in a dictionary object
		event_list: List of possible actions that can be runself.
		messages: Any error or sucessful messages to be presented to the user}

	To-do:
		*Change the agent list from straight dictrionary key= profile_id, value= first_name last_name, to a array of dictionaries
		*Change the if statemet checking the if action in the POST object. It should just check if there is a POST and then validate the fields inside
		*Change the parameters of the Shcedule meetings from being saved in the db to being passed to the function itself
	'''

	# Obtain all active agents
	agents = User.objects.filter(groups__name = 'Agent').filter(is_active=True)

	# Initiate the dictionary of agents and add an All option
	agent_list = {0:"All"}

	# Capture the timezone of the current user to manage dates the user selects and dates the system will display
	tz = pytz.timezone(request.user.profile.location.iso_name)

	# Initiate the object to hold any messages to the user
	messages = {}

	# Transform the Django query into a dictionary list
	for a in agents:
		agent_list[a.pk] = a.first_name + " " + a.last_name

	# Actions that can be schedule to be done, key is the value of the select list and the value is the text o display
	event_list = {"Add_Breaks_and_Lunches":"Add Breaks and Lunches",
			"Optimize_Breaks_and_Lunches":"Optimize Breaks and Lunches",
			"Schedule_a_Meeting":"Schedule a Meeting",
			"Insert_Shifts":"Insert Shifts",
			"Insert_Shifts_&_Breaks":"Insert Shifts and add Breaks"}

	# Check if the form has been submitted and there is an action
	# To be changed
	if 'action' in request.POST:

		# Capture the selection for each field, action, from what time to what time it needs to run and the agents it needs to run for
		actions = request.POST.getlist('action')
		start_date = request.POST.getlist('from')
		end_date = request.POST.getlist('to')
		agent = request.POST.getlist('agent')

		# Convert datetime of start and end selections from string to a datetime object and localize it to the timezone of the user
		start_date = datetime.strptime(start_date[0], '%d %B, %Y')
		start_date = tz.localize(start_date)

		end_date = datetime.strptime(end_date[0], '%d %B, %Y')
		end_date = tz.localize(end_date) + timedelta(days=1)

		# Get the job status object to use in the job object
		st = Job_Status.objects.get(name="Queued")

		# Initialize a variable to hold any parameters to be used by the job
		param = None

		if actions[0] == "Schedule_a_Meeting":
			''' Define the parameters to be abnle to schedule a meeting,
			such as the number of the people to schedule
			in each session, any notes, whether to move breaks / lunches / meetings and the duration of the meeting
			'''
			group_size = request.POST['group_size']
			notes = request.POST['meeting_notes']
			event = request.POST['event']
			override = None
			duration = request.POST['duration']
			if "override" in request.POST:
				override = request.POST['override']

			param = {"group_size": group_size, "override" : override, "notes": notes, "event": event, "duration":duration}

		# Save the job for each agent selected. If All was selected the agetns is = 0 which no agent has.
		for a in agent:
			j = Job(job_type = actions[0],
				from_date = start_date,
				to_date = end_date,
				agents = a,
				status = st,
				actioned_by = request.user,
				parameters = json.dumps(param))

			j.save()

			# Log the request for each job saved with al the parameters selected
			l_t = Log_Type.objects.get(name = "Add_Job")
			log_info = {"job_type": str(j.job_type), "from_date": str(j.from_date), "to_date": str(j.to_date), "agents": str(j.agents), "status": str(j.status), "actioned_by": str(j.actioned_by)}
			l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
			l.save()

		# Register a successful message
		messages['The job ' + request.POST['action'] + ' has been saved'] = "green"

		# Call each function depending on the event
		if actions[0] == 'Insert_Shifts':
			runsaveShift()
		elif actions[0] == 'Add_Breaks_and_Lunches':
			runsaveBreaks()
		elif actions[0] == 'Insert_Shifts_&_Breaks':
			runsaveShiftBreaks()
		elif actions[0] == 'Schedule_a_Meeting':
			runsaveMeetings()

	return render(request, 'wfm/add_exceptions.html', {'agent_list': agent_list, 'event_list': event_list, "messages": messages})

def set_timezone(request):
	if request.method == 'POST':
		request.session['django_timezone'] = request.POST['timezone']
		return redirect('/')
	else:
		return render(request, 'wfm/tz.html', {'timezones': pytz.common_timezones})

# Create your views here.
@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'Agent']).exists())
def calendar(request):
	return render(request, 'wfm/default.html', {"actions":request_actions,})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def calendar_team(request):
	return render(request, 'wfm/calendar_team.html', {"actions": request_actions,})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def calendar_manage(request):
	return render(request, 'wfm/calendar_manage.html', {"actions":request_actions,})

def events(request, sDate = False, eDate = False):
	schedule = getShifts(request)
	return JsonResponse(schedule, safe=False)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def team_events(request, sDate = False, eDate = False):
	schedule = getTeamShifts(request)
	return JsonResponse(schedule, safe=False)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def general_team_events(request, sDate = False, eDate = False):
	schedule = getGeneralTeamShifts(request)
	return JsonResponse(schedule, safe=False)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def manage_events(request, sDate = False, eDate = False):
	schedule = getAllShifts(request)
	return JsonResponse(schedule, safe=False)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def manage_exceptions(request, sDate = False, eDate = False):
	schedule = getAllExceptions(request)
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
	#print(exceptions.query)
	schedule = []
	events = {}

	for e in exceptions:
		date_e = e.start_date_time.astimezone(tzo).strftime("%Y-%m-%d")
		ev = {"title": e.event.name, "start":e.start_date_time.astimezone(tzo).strftime("%Y-%m-%d %H:%M:%S"), "end":e.end_date_time.astimezone(tzo).strftime("%Y-%m-%d %H:%M:%S"), "color":e.event.color, "textColor":e.event.text_color, "id":e.pk}

		if date_e not in events:
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

			schedule.append({"start": start_d.strftime("%Y-%m-%d %H:%M:%S"), "end": end_d.strftime("%Y-%m-%d %H:%M:%S"), "title":"Shift", "color":"#008288", "textColor":"#fff"})

		start = start + timedelta(days=1)

	return schedule

def getAllShifts(request):
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

	exceptions = Shift_Exception.objects.filter(approved=True)
	exceptions = exceptions.filter(start_date_time__gte=start)
	exceptions = exceptions.filter(end_date_time__lt=end)

	schedule = []
	events = {}


	while start < end:
		start_query = start
		start_format = start.astimezone(tzo).strftime("%Y-%m-%d")
		end_query = start_query + timedelta(days=1)

		sh_f = Shift_Sequence.objects.filter(Q(start_date_time__range = (start_query, end_query)) |  Q(end_date_time__range = (start_query, end_query)) )

		for sh1 in sh_f:
			start_d = sh1.start_date_time.astimezone(tzo)
			end_d = sh1.end_date_time.astimezone(tzo)
			event_user = "Shift " + sh1.user.user.first_name + " " + sh1.user.user.last_name

			if start_d < start:
				start_d = start
			if end_d > (start + timedelta(days=1)):
				end_d = (start + timedelta(days=1))

			schedule.append({"title": event_user,"start": start_d.strftime("%Y-%m-%d %H:%M:%S"), "end": end_d.strftime("%Y-%m-%d %H:%M:%S"), "color":"#008288", "textColor":"#fff"})

		start = start + timedelta(days=1)

	return schedule

def getAllExceptions(request):
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

	exceptions = Shift_Exception.objects.filter(approved=True)
	exceptions = exceptions.filter(start_date_time__gte=start)
	exceptions = exceptions.filter(end_date_time__lt=end)

	schedule = []
	events = {}

	for e in exceptions:
		date_e = e.start_date_time.astimezone(tzo).strftime("%Y-%m-%d")
		event_user = e.event.name + " " + e.user.user.first_name + " " + e.user.user.last_name
		ev = {"title": event_user, "start":e.start_date_time.astimezone(tzo).strftime("%Y-%m-%d %H:%M:%S"), "end":e.end_date_time.astimezone(tzo).strftime("%Y-%m-%d %H:%M:%S"), "color":e.event.color, "textColor":e.event.text_color, "id":e.pk}

		if date_e not in events:
			events[date_e] = []
		events[date_e].append(ev)

	while start < end:
		start_query = start
		start_format = start.astimezone(tzo).strftime("%Y-%m-%d")
		end_query = start_query + timedelta(days=1)

		if start_format in events:
			for e in events[start_format]:
				schedule.append(e)

		start = start + timedelta(days=1)

	return schedule

def getResources(request):

	all_supervisors = Profile.objects.filter(user__groups__name = 'Supervisor').filter(user__is_active = True)
	schedule = []
	#resource_cc = {}
	#resource_cc['id'] = "CC"
	#resource_cc['title'] = "Contact Center"
	#schedule.append(resource_cc)
	for sup in all_supervisors:
		resource_cc = {}
		resource_cc['id'] = str(sup.user.pk)
		resource_cc['title'] = sup.user.first_name + " " + sup.user.last_name
		all_users = Profile.objects.filter(user__groups__name = 'Agent').filter(team_manager = sup.user).filter(user__is_active = True)
		schedule.append(resource_cc)

		for us in all_users:
			resource_cc = {}
			resource_cc['id'] = str(us.user.pk)
			resource_cc['title'] = us.user.first_name + " " + us.user.last_name
			resource_cc['parentId'] = str(us.team_manager.pk)

			schedule.append(resource_cc)

	return JsonResponse(schedule, safe=False)

def getTeamShifts(request):
	all_users = Profile.objects.filter(user__groups__name = 'Agent').filter(user__is_active = True)

	schedule = []

	tz = pytz.timezone(request.user.profile.location.iso_name)

	for profile in all_users:

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
			ev = {"title": e.event.name, "start":e.start_date_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), "end":e.end_date_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), "color":e.event.color, "textColor":e.event.text_color, "id":e.pk, "resourceId": str(profile.user.pk)}

			if date_e not in events:
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
			#sh_f = Shift_Sequence.objects.filter(Q(user= profile), Q(start_date_time__range = (start_query, end_query))  )
			for sh1 in sh_f:
				start_d = sh1.start_date_time.astimezone(tz)
				end_d = sh1.end_date_time.astimezone(tz)

				if start_d.date() < start.date():
					start_d = start.replace(hour=0, minute=0)
				if end_d.date() > start.date():
					end_d = end_d.replace(hour=0, minute=0)

				schedule.append({"start": start_d.strftime("%Y-%m-%d %H:%M:%S"), "end": end_d.strftime("%Y-%m-%d %H:%M:%S"), "title":"Shift", "id":sh1.pk, "resourceId": str(profile.user.pk), "color":"#008288", "textColor":"#fff"})

			start = start + timedelta(days=1)



	return schedule

def getGeneralResources(request):

	all_agents = Profile.objects.filter(user__groups__name = 'Agent').filter(user__is_active = True)
	schedule = []
	#resource_cc = {}
	#resource_cc['id'] = "CC"
	#resource_cc['title'] = "Contact Center"
	#schedule.append(resource_cc)
	for ag in all_agents:
		resource_cc = {}
		resource_cc['id'] = str(ag.user.pk)
		resource_cc['title'] = ag.user.first_name + " " + ag.user.last_name
		schedule.append(resource_cc)

	return JsonResponse(schedule, safe=False)

def getGeneralTeamShifts(request):
	all_users = Profile.objects.filter(user__groups__name = 'Agent').filter(user__is_active = True)

	schedule = []

	tz = pytz.timezone(request.user.profile.location.iso_name)

	for profile in all_users:

		start = date.today()
		end = last_day_of_month(date.today())

		if 'start' in request.GET and request.GET['start']:
			start = request.GET['start'][:10]
			start = tz.localize(datetime.strptime(start, '%Y-%m-%d'))


		if 'end' in request.GET and request.GET['end']:
			end = request.GET['end'][:10]
			end = tz.localize(datetime.strptime(end, '%Y-%m-%d'))

		exceptions = Shift_Exception.objects.filter(user=profile).exclude(event__group__name = 'Overtime').filter(approved=True).filter(start_date_time__gte=start).filter(end_date_time__lte=end)

		events = {}

		for e in exceptions:
			date_e = e.start_date_time.astimezone(tz).strftime("%Y-%m-%d")
			ev = {"title": "Unavailable", "start":e.start_date_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), "end":e.end_date_time.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"), "color":"#a9abad", "textColor":"#000", "id":e.pk, "resourceId": str(profile.user.pk)}

			if date_e not in events:
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
			#sh_f = Shift_Sequence.objects.filter(Q(user= profile), Q(start_date_time__range = (start_query, end_query))  )
			for sh1 in sh_f:
				start_d = sh1.start_date_time.astimezone(tz)
				end_d = sh1.end_date_time.astimezone(tz)

				if start_d.date() < start.date():
					start_d = start.replace(hour=0, minute=0)
				if end_d.date() > start.date():
					end_d = end_d.replace(hour=0, minute=0)

				schedule.append({"start": start_d.strftime("%Y-%m-%d %H:%M:%S"), "end": end_d.strftime("%Y-%m-%d %H:%M:%S"), "title":"Shift", "id":sh1.pk, "resourceId": str(profile.user.pk), "color":"#008288", "textColor":"#fff"})

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

			l_t = Log_Type.objects.get(name = "Add_Agent")
			log_info = {"User":new_agent.user, "first_name": new_agent.first_name, "last_name": new_agent.last_name, "groups":new_agent.groups}
			l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
			l.save()

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

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'Agent']).exists())
def add_event(request, ev=False):

	messages = {}
	tz = pytz.timezone(request.user.profile.location.iso_name)
	cuser = request.user

	events = ""
	if not ev:
		events = Event.objects.exclude(group__name = 'Break').exclude(name = 'Stat Holiday').exclude(name = "AWOL")
	else:
		events = Event.objects.filter(group__name = str(ev))
	event_list = {}
	for e in events:
		event_list[e.pk] = e.name

	if request.POST:

		eve = ''
		from_date = ''
		to_date = ''
		from_time = ''
		to_time = ''
		notes = ''
		all_day = request.POST['all_day']

		if len(request.POST['event']) < 1:
			messages['Please select an activity'] = "red"
		else:
			eve = request.POST['event']

		if len(request.POST['from']) < 1:
			messages['Please select a start date'] = "red"
		else:
			from_date = request.POST['from']

		if len(request.POST['to']) < 1:
			messages['Please select an end date'] = "red"
		else:
			to_date = request.POST['to']

		if len(request.POST['from_time']) < 1 and request.POST['all_day'] == "No":
			messages['Please select a start time or set the all day dropdown to Yes'] = "red"
		elif request.POST['all_day'] == "Yes":
			from_time = '12:00AM'
		else:
			from_time = request.POST['from_time']

		if len(request.POST['to_time']) < 1 and request.POST['all_day'] == "No":
			messages['Please select an end timeor set the all day dropdown to Yes'] = "red"
		elif request.POST['all_day'] == "Yes":
			to_time = '11:59PM'
		else:
			to_time = request.POST['to_time']

		if len(request.POST['notes']) < 1:
			messages['Please provide a note'] = "red"
		else:
			notes = request.POST['notes']

		form_data = {
			"event": eve,
			"all_day": all_day,
			"from": from_date,
			"from_time": from_time,
			"to": to_date,
			"to_time": to_time,
			"notes": notes,
			}

		if len(messages) > 0:
			return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data})

		from_dt = datetime.strptime(from_date + " " + from_time, '%d %B, %Y %I:%M%p')
		from_dt = tz.localize(from_dt)

		to_dt = datetime.strptime(to_date + " " + to_time, '%d %B, %Y %I:%M%p')
		to_dt = tz.localize(to_dt)

		profile = cuser.profile

		total_time = to_dt - from_dt
		total_days = total_time.days

		eve_obj = Event.objects.get(pk = eve)
		print(to_dt)
		print(from_dt)
		ev = eve_obj.name

		if total_days > 1 and "Overtime" in ev:
			m = "You can not request OT for {0} days".format(total_days)
			messages[m] = "red"
			return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data})
		elif total_time.total_seconds() <= 0:
			m = "Please check you dates, these seem to be invalid"
			messages[m] = "red"
			return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data})
		elif total_time.total_seconds()/3600 < 4 and ev == "Vacation":
			m = "You can not request Vacation for less than 4 hours"
			messages[m] = "red"
			return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data})

		sh_f = ''
		s_diff = 0
		e_diff = to_dt - from_dt

		future_request = False

		try:
			sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__year = to_dt.year).filter(start_date_time__month = to_dt.month)
			if len(sh_f) == 0:
				future_request = True
			print("Not in the future")
		except:
			future_request = True

		no_valid_shift = False
		if not future_request:
			try:
				sh_f = Shift_Sequence.objects.filter(Q(user = profile) & ((Q(start_date_time__gte = from_dt) & Q(end_date_time__lte = to_dt)) | (Q(start_date_time__lte = from_dt) & Q(end_date_time__gte = to_dt))))
				print("found shift")
				print(sh_f)
				if len(sh_f) == 0:
					no_valid_shift = True
				print(no_valid_shift)
			except:
				no_valid_shift = True

			if no_valid_shift:
				if "Overtime" in ev:
					sh_f = Shift_Sequence.objects.filter(Q(user = profile) & ((Q(start_date_time__gte = from_dt) & Q(end_date_time__lte = to_dt)) | (Q(start_date_time__lte = from_dt) & Q(end_date_time__gte = to_dt))))
				else:
					m = "There is no shifts for this date range"
					messages[m] = "red"
					return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data})

		eve_obj = Event.objects.get(pk = eve)

		if not future_request:
			if "Overtime" in ev and len(sh_f) == 0:
				cu_from_dt = from_dt.astimezone(pytz.UTC)
				cu_to_dt = to_dt.astimezone(pytz.UTC)
				event_obj = Shift_Exception(user = profile, shift_sequence = None, event = eve_obj, start_date_time = cu_from_dt, start_diff = 0, end_date_time = cu_to_dt, end_diff = 0, approved=False, actioned_by = cuser, status = 0 )
				event_obj.save()

				l_t = Log_Type.objects.get(name = "Add_Event")
				log_info = {"user": str(profile), "shift_sequence": None, "event": str(eve_obj), "start_date_time": str(from_dt), "start_diff": str(0), "end_date_time": str(to_dt), "end_diff": str(0)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()

				n = Shift_Exception_Note(shift_exception = event_obj, note = notes, created_by = profile)
				n.save()

				l_t = Log_Type.objects.get(name = "Add_Event_Note")
				log_info = {"shift_exception": str(event_obj), "note": str(notes), "created_by": str(profile)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()
			else:
				for sh in sh_f:
					s_diff = 0
					e_diff = sh.end_date_time - sh.start_date_time

					cu_from_dt = from_dt.astimezone(pytz.UTC)
					cu_to_dt = to_dt.astimezone(pytz.UTC)

					#print(cu_from_dt)
					#print(cu_to_dt)
					#print(sh.start_date_time)
					#print(sh.end_date_time)

					if sh.start_date_time < cu_from_dt and cu_to_dt > sh.end_date_time and all_day == "Yes":
						continue

					if sh.end_date_time > cu_to_dt and cu_from_dt < sh.start_date_time and all_day == "Yes":
						continue

					if cu_from_dt < sh.start_date_time:
						cu_from_dt = sh.start_date_time

					if cu_to_dt > sh.end_date_time:
						cu_to_dt = sh.end_date_time

					#print(cu_from_dt)
					#print(cu_to_dt)
					#print(sh.start_date_time)
					#print(sh.end_date_time)


					event_obj = Shift_Exception(user = profile, shift_sequence = sh, event = eve_obj, start_date_time = cu_from_dt, start_diff = s_diff, end_date_time = cu_to_dt, end_diff = e_diff.days, approved=False, actioned_by = cuser, status = 0 )
					event_obj.save()

					l_t = Log_Type.objects.get(name = "Add_Event")
					log_info = {"user": str(profile), "shift_sequence": str(sh), "event": str(eve_obj), "start_date_time": str(from_dt), "start_diff": str(s_diff), "end_date_time": str(to_dt), "end_diff": str(e_diff.days)}
					l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
					l.save()

					n = Shift_Exception_Note(shift_exception = event_obj, note = notes, created_by = profile)
					n.save()

					l_t = Log_Type.objects.get(name = "Add_Event_Note")
					log_info = {"shift_exception": str(event_obj), "note": str(notes), "created_by": str(profile)}
					l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
					l.save()
		else:
			from_dt = from_dt.replace(hour = 8, minute = 0, second = 0)
			to_dt = to_dt.replace(hour = 4, minute = 30, second = 0)
			while s_diff <= e_diff.days:
				tmp_from_dt =  from_dt + timedelta(days = s_diff)
				tmp_to_dt = from_dt + timedelta(days = s_diff)
				tmp_to_dt = tmp_to_dt.replace(hour = 4, minute = 30, second = 0)

				event_obj = Shift_Exception(user = profile, event = eve_obj, start_date_time = tmp_from_dt, start_diff = 0, end_date_time = tmp_to_dt, end_diff = 0, approved=False, actioned_by = cuser, status = 0 )
				event_obj.save()

				s_diff += 1

				l_t = Log_Type.objects.get(name = "Add_Event")
				log_info = {"user": str(profile), "shift_sequence": str("Future request"), "event": str(eve_obj), "start_date_time": str(from_dt), "start_diff": str(s_diff), "end_date_time": str(to_dt), "end_diff": str(e_diff.days)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()

				n = Shift_Exception_Note(shift_exception = event_obj, note = notes, created_by = profile)
				n.save()

				l_t = Log_Type.objects.get(name = "Add_Event_Note")
				log_info = {"shift_exception": str(event_obj), "note": str(notes), "created_by": str(profile)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()

		messages['Your request has been submitted'] = "green"
	#print(agents)
	return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list,"messages":messages})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def add_request_manager(request, ev=False):

	messages = {}
	tz = pytz.timezone(request.user.profile.location.iso_name)
	cuser = request.user
	agents = []

	agents_obj = User.objects.filter(groups__name='Agent').filter(is_active=True).order_by('first_name')

	for agent in agents_obj:
		temp = {}
		temp['name'] = agent.first_name + " " + agent.last_name
		temp['id'] = agent.profile.id
		agents.append(temp)

	events = ""
	if not ev:
		events = Event.objects.all()
	else:
		events = Event.objects.filter(group__name = str(ev))
	event_list = {}
	for e in events:
		event_list[e.pk] = e.name

	if request.POST:

		eve = ''
		from_date = ''
		to_date = ''
		from_time = ''
		to_time = ''
		notes = ''
		agent = ''
		all_day = request.POST['all_day']

		if len(request.POST['agent']) < 1:
			message['Please select an agent'] = 'red'
		else:
			agent = request.POST['agent']

		if len(request.POST['event']) < 1:
			messages['Please select an activity'] = "red"
		else:
			eve = request.POST['event']

		if len(request.POST['from']) < 1:
			messages['Please select a start date'] = "red"
		else:
			from_date = request.POST['from']

		if len(request.POST['to']) < 1:
			messages['Please select an end date'] = "red"
		else:
			to_date = request.POST['to']

		if len(request.POST['from_time']) < 1 and request.POST['all_day'] == "No":
			messages['Please select a start time or set the all day dropdown to Yes'] = "red"
		elif request.POST['all_day'] == "Yes":
			from_time = '12:00AM'
		else:
			from_time = request.POST['from_time']

		if len(request.POST['to_time']) < 1 and request.POST['all_day'] == "No":
			messages['Please select an end timeor set the all day dropdown to Yes'] = "red"
		elif request.POST['all_day'] == "Yes":
			to_time = '11:59PM'
		else:
			to_time = request.POST['to_time']

		if len(request.POST['notes']) < 1:
			messages['Please provide a note'] = "red"
		else:
			notes = request.POST['notes']

		form_data = {'agent': agent,
			"event": eve,
			"all_day": all_day,
			"from": from_date,
			"from_time": from_time,
			"to": to_date,
			"to_time": to_time,
			"notes": notes,
			}

		if len(messages) > 0:
			return render(request, 'wfm/management_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data, "agents":agent})

		from_dt = datetime.strptime(from_date + " " + from_time, '%d %B, %Y %I:%M%p')
		from_dt = tz.localize(from_dt)

		to_dt = datetime.strptime(to_date + " " + to_time, '%d %B, %Y %I:%M%p')
		to_dt = tz.localize(to_dt)

		profile = Profile.objects.get(pk = agent)

		total_time = to_dt - from_dt
		total_days = total_time.days

		eve_obj = Event.objects.get(pk = eve)
		print(to_dt)
		print(from_dt)
		ev = eve_obj.name

		if total_days > 1 and "Overtime" in ev:
			m = "You can not request OT for {0} days".format(total_days)
			messages[m] = "red"
			return render(request, 'wfm/management_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data, "agents": agents})
		elif total_time.total_seconds() <= 0:
			m = "Please check you dates, these seem to be invalid"
			messages[m] = "red"
			return render(request, 'wfm/management_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data, "agents": agents})

		sh_f = ''
		s_diff = 0
		e_diff = to_dt - from_dt

		future_request = False

		try:
			sh_f = Shift_Sequence.objects.filter(Q(user = profile) & ((Q(start_date_time__gte = from_dt) & Q(end_date_time__lte = to_dt)) | (Q(start_date_time__lte = from_dt) & Q(end_date_time__gte = to_dt))))
			if len(sh_f) == 0:
				future_request = True
			print("Not in the future")
		except:
			future_request = True

		no_valid_shift = False
		if not future_request:
			try:
				sh_f = Shift_Sequence.objects.filter(Q(user = profile) & ((Q(start_date_time__gte = from_dt) & Q(end_date_time__lte = to_dt)) | (Q(start_date_time__lte = from_dt) & Q(end_date_time__gte = to_dt))))
				#print(sh_f.query)
				if len(sh_f) == 0:
					no_valid_shift = True
			except:
				no_valid_shift = True

			if no_valid_shift:
				if "Overtime" in ev:
					sf_f_s = Shift_Sequence.objects.filter(user = profile).filter(start_date_time = to_dt)
					if len(sf_f_s) > 0:
						sf_f_s[0].start_date_time = from_dt
						sf_f_s[0].save()

					sf_f_e = Shift_Sequence.objects.filter(user = profile).filter(end_date_time = from_dt)
					if len(sf_f_e) > 0:
						sf_f_e[0].end_date_time = to_dt
						sf_f_e[0].save()

					sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__lte = from_dt).filter(end_date_time__gte = to_dt)

					if len(sh_f) == 0:
						sh_f_n = Shift_Sequence(user = profile, start_date_time = from_dt, start_diff = s_diff, end_date_time = to_dt, end_diff = e_diff.days, actioned_by = cuser)
						sh_f_n.save()
						print("new shift")
						print(sh_f)
						sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__lte = to_dt).filter(end_date_time__gte = from_dt)
				else:
					m = "There is no shifts for this date range"
					messages[m] = "red"
					return render(request, 'wfm/management_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data, "agents": agents})

		eve_obj = Event.objects.get(pk = eve)

		if not future_request:
			for sh in sh_f:
				s_diff = 0
				e_diff = sh.end_date_time - sh.start_date_time

				cu_from_dt = from_dt.astimezone(pytz.UTC)
				cu_to_dt = to_dt.astimezone(pytz.UTC)

				#print(cu_from_dt)
				#print(cu_to_dt)
				#print(sh.start_date_time)
				#print(sh.end_date_time)

				if sh.start_date_time < cu_from_dt and cu_to_dt > sh.end_date_time and all_day == "Yes":
					continue

				if sh.end_date_time > cu_to_dt and cu_from_dt < sh.start_date_time and all_day == "Yes":
					continue

				if cu_from_dt < sh.start_date_time:
					cu_from_dt = sh.start_date_time

				if cu_to_dt > sh.end_date_time:
					cu_to_dt = sh.end_date_time

				#print(cu_from_dt)
				#print(cu_to_dt)
				#print(sh.start_date_time)
				#print(sh.end_date_time)


				event_obj = Shift_Exception(user = profile, shift_sequence = sh, event = eve_obj, start_date_time = cu_from_dt, start_diff = s_diff, end_date_time = cu_to_dt, end_diff = e_diff.days, approved=True, actioned_by = cuser, status = 1 )
				event_obj.save()

				l_t = Log_Type.objects.get(name = "Add_Event")
				log_info = {"user": str(profile), "shift_sequence": str(sh), "event": str(eve_obj), "start_date_time": str(from_dt), "start_diff": str(s_diff), "end_date_time": str(to_dt), "end_diff": str(e_diff.days)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()

				n = Shift_Exception_Note(shift_exception = event_obj, note = notes, created_by = profile)
				n.save()

				l_t = Log_Type.objects.get(name = "Add_Event_Note")
				log_info = {"shift_exception": str(event_obj), "note": str(notes), "created_by": str(profile)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()
		else:
			from_dt = from_dt.replace(hour = 8, minute = 0, second = 0)
			to_dt = to_dt.replace(hour = 4, minute = 30, second = 0)
			while s_diff <= e_diff.days:
				tmp_from_dt =  from_dt + timedelta(days = s_diff)
				tmp_to_dt = from_dt + timedelta(days = s_diff)
				tmp_to_dt = tmp_to_dt.replace(hour = 4, minute = 30, second = 0)

				event_obj = Shift_Exception(user = profile, event = eve_obj, start_date_time = tmp_from_dt, start_diff = 0, end_date_time = tmp_to_dt, end_diff = 0, approved=True, actioned_by = cuser, status = 1 )
				event_obj.save()

				s_diff += 1

				l_t = Log_Type.objects.get(name = "Add_Event")
				log_info = {"user": str(profile), "shift_sequence": str("Future request"), "event": str(eve_obj), "start_date_time": str(from_dt), "start_diff": str(s_diff), "end_date_time": str(to_dt), "end_diff": str(e_diff.days)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()

				n = Shift_Exception_Note(shift_exception = event_obj, note = notes, created_by = profile)
				n.save()

				l_t = Log_Type.objects.get(name = "Add_Event_Note")
				log_info = {"shift_exception": str(event_obj), "note": str(notes), "created_by": str(profile)}
				l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
				l.save()

		messages['Your request has been submitted'] = "green"
	#print(agents)
	return render(request, 'wfm/management_event.html', {"actions": request_actions, "event_list":event_list,"messages":messages,"agents":agents})



@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def review_requests(request):
	messages = {}

	user_profile = Profile.objects.get(user = request.user)

	tz = pytz.timezone(request.user.profile.location.iso_name)

	all_users = Profile.objects.filter(user__groups__name = 'Agent').filter(user__is_active=True)

	status ={"pending":"Pending", "approved":"Approved","rejected":"Rejected","deleted":"Deleted"}

	agents = {}

	r_type = {"Meeting":"Meeting","Timeoff":"Timeoff","Overtime":"Overtime"}

	for user in all_users:
		agents[user.pk] = user.user.first_name + " " + user.user.last_name

	if request.POST:

		agent_id = ""
		st_type = ""
		st_status = ""

		form_data = {}

		if 'agent_id' in request.POST:
			agent_id = request.POST['agent_id']
			form_data['agent_id'] = agent_id

		if 'type' in request.POST:
			st_type = request.POST['type']
			form_data['type'] = st_type

		if 'status' in request.POST:
			st_status = request.POST['status']
			form_data['status'] = st_status

		from_d = request.POST['from']
		to_d = request.POST['to']

		form_data['from'] = from_d
		form_data['to'] = to_d

		start_date = True
		end_date = True

		if len(from_d) < 1:
			start_date = False

		if len(to_d) < 1:
			end_Date = False

		if len(messages) > 0:
			return render(request, 'wfm/review_request.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "fields": form_data, "profile":user_profile.pk})

		req = None
		if start_date and end_date:
			from_dt = datetime.strptime(from_d, '%d %B, %Y')
			to_dt = datetime.strptime(to_d, '%d %B, %Y')

			from_dt = tz.localize(from_dt)
			to_dt = tz.localize(to_dt) + timedelta(days=1)

			req = Shift_Exception.objects.filter(submitted_time__gte = from_dt.astimezone(pytz.UTC)).filter(submitted_time__lte = to_dt.astimezone(pytz.UTC)).exclude(event__group__name = 'Break')

		else:
			req = Shift_Exception.objects.exclude(event__group__name = 'Break').order_by('-submitted_time', 'start_date_time')

		if len(agent_id) > 0:
			req = req.filter(user__id = agent_id)

		if len(st_status) > 0:
			if st_status == "pending":
				req = req.filter(status = 0)
			elif st_status == "approved":
				req = req.filter(status = 1)
			elif st_status == "deleted":
				req = req.filter(status = 3)
			else:
				req = req.filter(status = 2)

		if len(st_type) > 0:
			req = req.filter(event__group__name = st_type)

		if st_status != "pending":
			req = req.order_by('-id', 'start_date_time')
			req = req[:100]
		else:
			req = req.order_by('id', 'start_date_time')
		results = []
		for r in req:
			values = []
			values.append(r.pk)
			values.append(r.event)
			values.append(r.user)

			if r.status == 0:
				values.append("Pending")
			elif r.status == 1:
				values.append("Approved")
			elif r.status == 2:
				values.append("Rejected")
			else:
				values.append("Deleted")

			values.append(r.submitted_time.astimezone(tz).strftime('%x %X'))
			values.append(r.actioned_by.first_name + " " + r.actioned_by.last_name)

			values.append(r.start_date_time.astimezone(tz).strftime('%x %X'))
			values.append(r.end_date_time.astimezone(tz).strftime('%x %X'))
			all_notes = []

			try:
				notes = Shift_Exception_Note.objects.filter(shift_exception = r).order_by('-created_time')
				for n in notes:
					grop = n.created_by.user.groups.values_list('name', flat=True)
					if "Admin" in grop:
						all_notes.append(datetime.strftime(n.created_time.astimezone(tz), "%c") + " by WFM Admin: " + n.note)
					else:
						all_notes.append(datetime.strftime(n.created_time.astimezone(tz), "%c") + " by " + n.created_by.user.first_name + " " + n.created_by.user.last_name + ": " + n.note)

				if len(notes) == 0:
					all_notes.append("No Notes")

			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print(exc_type, fname, exc_tb.tb_lineno)
				all_notes.append("No Notes")

			#print(values)
			results.append({'id': r.pk, 'values': values, 'notes': all_notes})
		#print req.query
		#print len(req)
		#print results
		return render(request, 'wfm/review_request.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "results": results, "fields": form_data, "profile":user_profile.pk})

	return render(request, 'wfm/review_request.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "profile":user_profile.pk})

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'Agent']).exists())
def review_requests_agent(request):
	messages = {}

	user_profile = Profile.objects.get(user = request.user)

	tz = pytz.timezone(request.user.profile.location.iso_name)


	status ={"pending":"Pending", "approved":"Approved","rejected":"Rejected"}

	agents = {}

	r_type = {"Meeting":"Meeting","Timeoff":"Timeoff","Overtime":"Overtime"}

	agents[request.user.profile.pk] = request.user.first_name + " " + request.user.last_name

	if request.POST:

		agent_id = ""
		st_type = ""
		st_status = ""

		form_data = {}

		if 'agent_id' in request.POST:
			agent_id = request.POST['agent_id']
			form_data['agent_id'] = agent_id

		if 'type' in request.POST:
			st_type = request.POST['type']
			form_data['type'] = st_type

		if 'status' in request.POST:
			st_status = request.POST['status']
			form_data['status'] = st_status

		from_d = request.POST['from']
		to_d = request.POST['to']

		form_data['from'] = from_d
		form_data['to'] = to_d

		start_date = False
		end_date = False

		if len(from_d) < 1:
			start_date = True

		if len(to_d) < 1:
			end_Date = False

		if len(messages) > 0:
			return render(request, 'wfm/review_request_agent.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "fields": form_data, "profile":user_profile.pk})

		req = None
		if start_date and end_date:
			from_dt = datetime.strptime(from_d, '%d %B, %Y')
			to_dt = datetime.strptime(to_d, '%d %B, %Y')

			from_dt = tz.localize(from_dt)
			to_dt = tz.localize(to_dt) + timedelta(days=1)

			req = Shift_Exception.objects.filter(submitted_time__gte = from_dt.astimezone(pytz.UTC)).filter(submitted_time__lte = to_dt.astimezone(pytz.UTC)).exclude(event__group__name = 'Break').order_by('-submitted_time', 'start_date_time')

		else:
			req = Shift_Exception.objects.exclude(event__group__name = 'Break').order_by('-submitted_time', 'start_date_time')

		if len(agent_id) > 0:
			req = req.filter(user__id = agent_id)

		if len(st_status) > 0:
			if st_status == "pending":
				req = req.filter(status = 0)
			elif st_status == "approved":
				req = req.filter(status = 1)
			else:
				req = req.filter(status = 2)

		if len(st_type) > 0:
			req = req.filter(event__group__name = st_type)
		#print(req.query)
		req = req[:20]
		results = []
		for r in req:
			values = []
			values.append(r.pk)
			values.append(r.event)
			values.append(r.user)

			if r.status == 0:
				values.append("Pending")
			elif r.status == 1:
				values.append("Approved")
			else:
				values.append("Rejected")

			values.append(r.submitted_time.astimezone(tz).strftime('%x %X'))
			values.append(r.actioned_by.first_name + " " + r.actioned_by.last_name)

			values.append(r.start_date_time.astimezone(tz).strftime('%x %X'))
			values.append(r.end_date_time.astimezone(tz).strftime('%x %X'))
			all_notes = []

			try:
				notes = Shift_Exception_Note.objects.filter(shift_exception = r).order_by('-created_time')

				for n in notes:
					grop = n.created_by.user.groups.values_list('name', flat=True)
					if "Admin" in grop:
						all_notes.append(datetime.strftime(n.created_time.astimezone(tz), "%c") + " by WFM Admin: " + n.note)
					else:
						all_notes.append(datetime.strftime(n.created_time.astimezone(tz), "%c") + " by " + n.created_by.user.first_name + " " + n.created_by.user.last_name + ": " + n.note)

				if len(notes) == 0:
					all_notes.append("No Notes")

			except Exception as e:
				#print(e)
				all_notes.append("No Notes")

			#print(values)
			results.append({'id': r.pk, 'values': values, 'notes': all_notes})
		#print req.query
		#print len(req)
		#print results
		return render(request, 'wfm/review_request_agent.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "results": results, "fields": form_data, "profile":user_profile.pk})

	return render(request, 'wfm/review_request_agent.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "profile":user_profile.pk})


def agentBoard(request):
	return render(request, 'wfm/agent.html', {"actions":request_actions,})

@csrf_exempt
def changeException(request):
	if request.body:
		data = json.loads(request.body)
		print(data)
		p = data['profile']
		e = data['event']
		t = data['title']
		delta = data['time_delta']
		start = datetime.strptime(data['start'], "%Y-%m-%dT%H:%M:%S")
		end = datetime.strptime(data['end'], "%Y-%m-%dT%H:%M:%S")

		tz = pytz.timezone(request.user.profile.location.iso_name)

		start = tz.localize(start)
		end = tz.localize(end)
		agent = User.objects.get(pk = p)

		#print(delta)
		if t == 'Shift':
			ev = Shift_Sequence.objects.get(pk = e)
			ev.start_date_time = start
			ev.end_date_time = end
			delta_days = end - start
			ev.end_diff = delta_days.days
			ev.save()

			exceptions = Shift_Exception.objects.filter(shift_sequence = ev)
			for ex in exceptions:
				ex.start_date_time = ex.start_date_time + timedelta(minutes = delta)
				ex.end_date_time = ex.end_date_time + timedelta(minutes = delta)
				ex.start_diff = 0
				delta_d = ex.end_date_time - ex.start_date_time
				ex.end_diff = delta_d.days
				ex.save()

			return JsonResponse({'Status':"OK", 'data':"Shift Sucessfully Changed For " + agent.first_name}, safe=False)
		else:
			ev = Shift_Exception.objects.get(pk = e)
			ev.start_date_time = start
			ev.end_date_time = end
			delta_days = end - start
			ev.end_diff = delta_days.days
			ev.save()
			data_info = t + " Sucessfully Changed For " + str(agent.first_name)
			return JsonResponse({'Status':"OK", 'data': data_info}, safe=False)
	return JsonResponse({'Status':"Failed",}, safe=False)

@csrf_exempt
def addEvent(request):
	if request.body:
		data = json.loads(request.body)

		p = data['profile']
		e = data['event']
		t = data['title']
		delta = data['time_delta']
		start = datetime.strptime(data['start'], "%Y-%m-%dT%H:%M:%S")
		end = datetime.strptime(data['end'], "%Y-%m-%dT%H:%M:%S")

		tz = pytz.timezone(request.user.profile.location.iso_name)

		start = tz.localize(start)
		end = tz.localize(end)
		agent = User.objects.get(pk = p)

		#print(delta)
		if t == 'Shift':
			ev = Shift_Sequence.objects.get(pk = e)
			ev.start_date_time = start
			ev.end_date_time = end
			delta_days = end - start
			ev.end_diff = delta_days.days
			ev.save()

			exceptions = Shift_Exception.objects.filter(shift_sequence = ev)
			for ex in exceptions:
				ex.start_date_time = ex.start_date_time + timedelta(minutes = delta)
				ex.end_date_time = ex.end_date_time + timedelta(minutes = delta)
				ex.start_diff = 0
				delta_d = ex.end_date_time - ex.start_date_time
				ex.end_diff = delta_d.days
				ex.save()

			return JsonResponse({'Status':"OK", 'data':"Shift Sucessfully Changed For " + agent.first_name}, safe=False)
		else:
			ev = Shift_Exception.objects.get(pk = e)
			ev.start_date_time = start
			ev.end_date_time = end
			delta_days = end - start
			ev.end_diff = delta_days.days
			ev.save()
			return JsonResponse({'Status':"OK", 'data':t + " Sucessfully Changed For " + agent.first_name}, safe=False)
	return JsonResponse({'Status':"Failed",}, safe=False)

@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def scheduleOneonOne(request):
	#lock from 11 to 19
	notifications = {}
	weeks = []

	for i in range(0,4):
		today = datetime.now() + timedelta(days=(i*7))
		start = today - timedelta(days=today.weekday())
		end = start + timedelta(days=6)
		value = start.strftime('%d/%b/%Y') + " - " + end.strftime('%d/%b/%Y')
		key = start.strftime('%d/%b/%Y')
		week = {'date': key, 'week': value}
		weeks.append(week)

	agent_list = []

	if request.POST:
		tz = pytz.timezone(request.user.profile.location.iso_name)

		start_week = request.POST['weekSelection']

		if not start_week:
			return render(request, 'wfm/oneonone.html', {"messages": notifications, "weeks": weeks})
		from_dt = datetime.strptime(start_week, '%d/%b/%Y')
		from_dt = tz.localize(from_dt)
		to_dt = from_dt + timedelta(days=6)

		agents = Profile.objects.filter(team_manager = request.user).filter(user__is_active = True).order_by('user__first_name', 'user__last_name')
		#print(len(agents))
		for agent in agents:
			a = {'id': agent.id, 'name': agent.user.first_name + " " + agent.user.last_name}
			skills = agent.skill_level.all()
			ski = []
			for sk in skills:
				sk_f = str(sk)

				if "Phone" in sk_f:
					sk_f = sk_f.replace(" - Phone","")
				else:
					continue
				sk_f = sk_f.split(" ")
				sk_f = sk_f[1]
				if sk_f != "English":
					ski.insert(0, sk_f)
				else:
					ski.append(sk_f)

			if len(ski) > 1 and "English" in ski:
				ind = ski.index("English")
				del ski[ind]
			shifts = Shift_Sequence.objects.filter(user = agent).filter(start_date_time__gte = from_dt).filter(end_date_time__lte = to_dt)
			slots = []
			for shift in shifts:
				slot = findBestTimes(ski, shift.start_date_time, shift.start_date_time, shift.end_date_time, 60, agent)
				if slot:
					slot_tmp = []
					for k, v in slot.items():
						slot_tmp.append(k.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"))
					sl_tmp = sorted(slot_tmp)
					data = {'date': shift.start_date_time.strftime("%Y-%m-%d"), 'slots': sl_tmp}
					slots.append(data)
			a['slots'] = slots

			agent_list.append(a)
	#print(agent_list)
	return render(request, 'wfm/oneonone.html', {"messages": notifications, "weeks": weeks, "agents": agent_list})

def findBestTimes(ski, b_date_format, b_time_start, b_time_end, duration, pro, override=False):
	#print("trying to connect")
	c = connection.cursor()
	#print("Trying to find time")
	duration = int(duration)

	b_time_start_format = b_time_start.strftime("%Y-%m-%d %H:%M:%S")
	#print(b_time_start_format)
	#b_time_end_format = b_time_end - timedelta(minutes = duration)
	b_time_end_format = b_time_end.strftime("%Y-%m-%d %H:%M:%S")
	#print(b_time_end_format)
	intervals = duration / 15
	#print(intervals)
	diff = {}
	#print("finding the best time")
	for sk in ski:
		#c.execute("SELECT `date`, (agents_required - actual_agents_scheduled) as d from forecast_call_forecast where `date` >= %s and `date` < %s and queue = %s", (b_time_start_format, b_time_end_format, sk))
		c.execute("SELECT `date`, actual_agents_scheduled as d from forecast_call_forecast where `date` >= %s and `date` <= %s and queue = %s", (b_time_start_format, b_time_end_format, sk))
		results = c.fetchall()
		#print(len(results))
		for r in results:
			date_out = pytz.utc.localize(r[0])
			if date_out not in diff:
				diff[date_out] = 0


		for r in results:
			i = 1
			total = 0
			date_out = pytz.utc.localize(r[0])
			while i <= intervals:
				m = 15 * i
				date_in = r[0] + timedelta(minutes=m)
				date_in = pytz.utc.localize(date_in)
				s_e = None
				try:
					s_e = Shift_Exception.objects.filter(Q(start_date_time__lte = date_out) & Q(end_date_time__gte = date_in) & Q(user=pro))
				except:
					s_e = None
				if len(s_e) > 0:
					#remove interval if there is an exception already
					if date_out in diff:
						del diff[date_out]
				elif date_in in diff:
					#add number of agents scheduled
					total = total + float(r[1])
				else:
					if date_out in diff:
						del diff[date_out]
				i += 1
			#add the number of agents to the interval
			if date_out in diff:
				diff[date_out] = diff[date_out] + total
	#print("slots")
	#print(diff)
	besttime = None
	lowestAgents = None
	for k, value in diff.items():
		if value > lowestAgents or not lowestAgents:
			lowestAgents = value
			besttime = k
	#print(besttime)
	c.close()
	#tzo = pytz.timezone("UTC")
	#besttime = tzo.localize(besttime)
	return diff
