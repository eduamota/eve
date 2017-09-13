# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from wfm.models import Shift, Profile, Day_Model, Shift_Exception, Event
from django.contrib.auth.models import User
from datetime import timedelta

# Create your views here.
def calendar(request):
	user = User.objects.get(username = "emota")
	profile = Profile.objects.get(user = user)
	shifts = Shift.objects.get(user=profile)
	day_model = Day_Model.objects.get(shift=shifts)
	exceptions = Shift_Exception.objects.get(user=profile)
	event = Event.objects.get(shift_exception=exceptions)
	
	working_days={
		"Sunday": shifts.sunday,
		"Monday": shifts.monday,
		"Tuesday": shifts.tuesday,
		"Wednesday": shifts.wednesday,
		"Thursday": shifts.thursday,
		"Friday": shifts.friday,
		"Saturday": shifts.saturday,									}

	schedule = {}
	
	start_date = shifts.valid_from
	end_date = shifts.valid_to
	
	print event.color
	
	day_start = day_model.day_start_time.strftime("%H:%M:%S")
	day_end = day_model.day_end_time.strftime("%H:%M:%S")
	
	while start_date <= end_date:
		
		dayName = start_date.strftime("%A")
		
		start_format = start_date + timedelta(days=int(day_model.day_start_diff))
		start_format = start_format.strftime("%Y-%m-%d")
		
		end_format = start_date + timedelta(days=int(day_model.day_end_diff))
		end_format = end_format.strftime("%Y-%m-%d")
		
		if working_days[dayName]:		
			schedule[start_format] = {"start": start_format + "T" + day_start, "end": end_format + "T" + day_end}
		start_date = start_date + timedelta(days=1)
		
	exceptions.start_date_time = exceptions.start_date_time.strftime("%Y-%m-%dT%H:%M:%S")
	exceptions.end_date_time = exceptions.end_date_time.strftime("%Y-%m-%dT%H:%M:%S")
	
	return render(request, 'shifts/default.html', {'shift_name':day_model.name, 'schedule':schedule, 'exceptions':exceptions, 'color':event.color})
