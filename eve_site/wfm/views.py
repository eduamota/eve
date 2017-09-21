# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from wfm.models import Shift, Profile, Shift_Exception, Event
from django.contrib.auth.models import User
from datetime import timedelta, datetime, date
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
	return next_month - timedelta(days=next_month.day)

@login_required
def add_events(request):
	agents = User.objects.filter(groups__name = 'Agent')
	agent_list = {0:"All"}

	for a in agents:
		agent_list[a.pk] = a.first_name + " " + a.last_name
		
	event_list = {"Add_Breaks_and_Lunches":"Add Breaks and Lunches","Optimize_Breaks_and_Lunches":"Optimize Breaks and Lunches","Schedule_a_Meeting":"Schedule a Meeting",}
	
	return render(request, 'shifts/add_exceptions.html', {'agent_list': agent_list, 'event_list': event_list,})
	
# Create your views here.
@login_required
def calendar(request):	
	return render(request, 'shifts/default.html')
	
def events(request):
	schedule = getShifts(request)
	return JsonResponse(schedule, safe=False)
	
def getShifts(request):
	current_user = request.user
	user = User.objects.get(username = current_user.username)
	profile = Profile.objects.get(user = user)
	
	start = date.today()
	end = last_day_of_month(date.today())
	
	if 'start' in request.GET and request.GET['start']:
		start = request.GET['start'][:10]
		start = datetime.strptime(start, '%Y-%m-%d').date()
		
	if 'end' in request.GET and request.GET['end']:
		end = request.GET['end'][:10]
		end = datetime.strptime(end, '%Y-%m-%d').date()
	
	shifts = Shift.objects.filter(user=profile)
	shifts = shifts.filter(valid_from__lte=end)
	shifts = shifts.filter(valid_to__gte=start)

	exceptions = Shift_Exception.objects.filter(user=profile)
	exceptions = exceptions.filter(approved=True)
	exceptions = exceptions.filter(start_date_time__gte=start)
	exceptions = exceptions.filter(end_date_time__lt=end)

	schedule = []
	events = {}

	for e in exceptions:
		date_e = e.start_date_time.date()
		ev = {"title": e.event.name, "start":e.start_date_time.strftime("%Y-%m-%d %H:%M:%S"), "end":e.end_date_time.strftime("%Y-%m-%d %H:%M:%S"), "color":e.event.color, "textColor":e.event.text_color, "id":e.event.pk}

		if not(events.has_key(date_e)):
			events[date_e] = []
		events[date_e].append(ev)
	
	for s in shifts:
		working_days={
			"Sunday": s.sunday,
			"Monday": s.monday,
			"Tuesday": s.tuesday,
			"Wednesday": s.wednesday,
			"Thursday": s.thursday,
			"Friday": s.friday,
			"Saturday": s.saturday,	
		}
		
		start_date = s.valid_from
		end_date = s.valid_to
		
		day_start = s.day_model.day_start_time.strftime("%H:%M:%S")
		day_end = s.day_model.day_end_time.strftime("%H:%M:%S")
		
		if start_date < start:
			start_date = start
		if end_date > end:
			end_date = end
		
		while start_date <= end_date:
			
			dayName = start_date.strftime("%A")
			
			start_format = start_date + timedelta(days=int(s.day_model.day_start_diff))
			start_format = start_format.strftime("%Y-%m-%d")
			
			end_format = start_date + timedelta(days=int(s.day_model.day_end_diff))
			end_format = end_format.strftime("%Y-%m-%d")
			
			if start_date in events:
				for e in events[start_date]:
					schedule.append(e)
			
			if working_days[dayName]:		
				schedule.append({"start": start_format + " " + day_start, "end": end_format + " " + day_end, "title":user.first_name})
				
			start_date = start_date + timedelta(days=1)
	
	return schedule	
	#return JsonResponse(schedule)
