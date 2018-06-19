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

request_actions = {"../request/Timeoff":"Request Time Off",
			"../request/Overtime":"Request Overtime",
			"../request/Meeting":"Request a 1-1 / Coaching",
								}

def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
	return next_month - timedelta(days=next_month.day)

@login_required
def schedule_job(request):
	'''

	'''
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

			l_t = Log_Type.objects.get(name = "Add_Job")
			log_info = {"job_type": str(j.job_type), "from_date": str(j.from_date), "to_date": str(j.to_date), "agents": str(j.agents), "status": str(j.status), "actioned_by": str(j.actioned_by)}
			l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
			l.save()

		messages['The job ' + request.POST['action'] + ' has been saved'] = "green"

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
@login_required
def calendar(request):
	return render(request, 'wfm/default.html', {"actions":request_actions,})

@login_required
def calendar_team(request):
	return render(request, 'wfm/calendar_team.html', {"actions": request_actions,})

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

			schedule.append({"start": start_d.strftime("%Y-%m-%d %H:%M:%S"), "end": end_d.strftime("%Y-%m-%d %H:%M:%S"), "title":"Shift", "color":"#008288", "textColor":"#fff"})

		start = start + timedelta(days=1)

	return schedule

def getResources(request):

	all_supervisors = Profile.objects.filter(user__groups__name = 'Supervisor')
	schedule = []
	#resource_cc = {}
	#resource_cc['id'] = "CC"
	#resource_cc['title'] = "Contact Center"
	#schedule.append(resource_cc)
	for sup in all_supervisors:
		resource_cc = {}
		resource_cc['id'] = str(sup.user.pk)
		resource_cc['title'] = sup.user.first_name + " " + sup.user.last_name
		all_users = Profile.objects.filter(user__groups__name = 'Agent').filter(team_manager = sup.user)
		schedule.append(resource_cc)

		for us in all_users:
			resource_cc = {}
			resource_cc['id'] = str(us.user.pk)
			resource_cc['title'] = us.user.first_name + " " + us.user.last_name
			resource_cc['parentId'] = str(us.team_manager.pk)

			schedule.append(resource_cc)

	return JsonResponse(schedule, safe=False)

def getTeamShifts(request):
	all_users = Profile.objects.filter(user__groups__name = 'Agent')

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
					end_d = start.replace(hour=23, minute=59)

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

@login_required
def add_event(request, ev=False):

	messages = {}
	tz = pytz.timezone(request.user.profile.location.iso_name)
	cuser = request.user.profile

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

		if len(request.POST['from_time']) < 1:
			messages['Please select a start time'] = "red"
		else:
			from_time = request.POST['from_time']

		if len(request.POST['to_time']) < 1:
			messages['Please select an end time'] = "red"
		else:
			to_time = request.POST['to_time']

		if len(request.POST['notes']) < 1:
			messages['Please provide a note'] = "red"
		else:
			notes = request.POST['notes']

		form_data = {"event": eve,
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

		profile = Profile.objects.get(user = request.user)

		total_time = to_dt - from_dt
		total_days = total_time.days

		if total_days > 1 and ev == "Overtime":
			m = "You can not request OT for {0} days".format(total_days)
			messages[m] = "red"
			return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data})
		elif total_time.total_seconds() <= 0:

			m = "Please check you dates, these seem to be invalid"
			messages[m] = "red"
			return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list, "messages":messages, "form_data": form_data})

		sh_f = ''
		s_diff = 0
		e_diff = to_dt - from_dt

		try:
			sh_f = Shift_Sequence.objects.filter(user = profile).filter(start_date_time__lte = to_dt).filter(end_date_time__gte = from_dt)[0]
		except:
			sh_f = Shift_Sequence(user = profile, start_date_time = from_dt, start_diff = s_diff, end_date_time = to_dt, end_diff = e_diff.days, actioned_by = cuser)
			sh_f.save()



		eve_obj = Event.objects.get(pk = eve)


		event_obj = Shift_Exception(user = profile, shift_sequence = sh_f, event = eve_obj, start_date_time = from_dt, start_diff = s_diff.days, end_date_time = to_dt, end_diff = e_diff.days, approved=False, actioned_by = cuser, status = 0 )

		event_obj.save()

		l_t = Log_Type.objects.get(name = "Add_Event")
		log_info = {"user": str(profile), "shift_sequence": str(sh_f), "event": str(eve_obj), "start_date_time": str(from_dt), "start_diff": str(s_diff.days), "end_date_time": str(to_dt), "end_diff": str(e_diff.days)}
		l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
		l.save()

		n = Shift_Exception_Note(shift_exception = event_obj, note = notes, created_by = profile)
		n.save()

		l_t = Log_Type.objects.get(name = "Add_Event_Note")
		log_info = {"shift_exception": str(event_obj), "note": str(notes), "created_by": str(profile)}
		l = Log(created_by = request.user, log_type = l_t, log_info = json.dumps(log_info))
		l.save()

		messages['Your request has been submitted'] = "green"

	return render(request, 'wfm/add_event.html', {"actions": request_actions, "event_list":event_list,"messages":messages})

@login_required
def review_requests(request):
	messages = {}

	user_profile = Profile.objects.get(user = request.user)

	tz = pytz.timezone(request.user.profile.location.iso_name)

	all_users = Profile.objects.filter(user__groups__name = 'Agent')

	status ={"pending":"Pending", "approved":"Approved","rejected":"Rejected"}

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

		if len(from_d) < 1:
			messages['Please indicate a date to start the search from'] = 'red'

		if len(to_d) < 1:
			messages['Please indicate a date to finish the search'] = 'red'

		if len(messages) > 0:
			return render(request, 'wfm/review_request.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "fields": form_data, "profile":user_profile.pk})

		from_dt = datetime.strptime(from_d, '%d %B, %Y')
		to_dt = datetime.strptime(to_d, '%d %B, %Y')

		from_dt = tz.localize(from_dt)
		to_dt = tz.localize(to_dt)

		req = Shift_Exception.objects.filter(submitted_time__gte = from_dt).filter(submitted_time__lte = to_dt)


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

			values.append(r.submitted_time)
			values.append(r.actioned_by.first_name + " " + r.actioned_by.last_name)

			values.append(r.start_date_time)
			values.append(r.end_date_time)

			all_notes = []

			try:
				notes = Shift_Exception_Note.objects.filter(shift_exception = r).order_by('-created_time')

				for n in notes:
					all_notes.append(datetime.strftime(n.created_time, "%c") + " by " + n.created_by.user.first_name + " " + n.created_by.user.last_name + ": " + n.note)

				if len(notes) == 0:
					all_notes.append("No Notes")

			except Exception as e:
				print(e)
				all_notes.append("No Notes")


			results.append({'id': r.pk, 'values': values, 'notes': all_notes})
		#print req.query
		#print len(req)
		#print results
		return render(request, 'wfm/review_request.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "results": results, "fields": form_data, "profile":user_profile.pk})

	return render(request, 'wfm/review_request.html', {"actions": request_actions, "messages":messages, "agents":agents, "type":r_type, "status":status, "profile":user_profile.pk})

def agentBoard(request):
	return render(request, 'wfm/agent.html', {"actions":request_actions,})

@csrf_exempt
def changeException(request):
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
