# -*- coding: utf-8 -*-
"""
Created on Fri Oct 13 09:10:00 2017

@author: emota
"""
from __future__ import unicode_literals

from wfm.models import Shift, Profile, Shift_Sequence
from django.contrib.auth.models import User
from datetime import timedelta, datetime, date

def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
	return next_month - timedelta(days=next_month.day)

def insertShifts(request):
	current_user = request.user
	user_inst = User.objects.get(username = current_user.username)
	profile = Profile.objects.get(user = user_inst)
	
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
			
			start_d_t = datetime.strptime(start_format + " " + day_start, "%Y-%m-%d %H:%M:%S")
			
			end_format = start_date + timedelta(days=int(s.day_model.day_end_diff))
			end_format = end_format.strftime("%Y-%m-%d")
			
			start_d_t = datetime.strptime(end_format + " " + day_end, "%Y-%m-%d %H:%M:%S")
			
			if working_days[dayName]:				
				s = Shift_Sequence(user = user_inst, start_date_time = start_d_t, start_diff = int(s.day_model.day_start_diff), end_date_time = start_d_t, end_diff = int(s.day_model.day_end_diff), actioned_by = user_inst)
				
				s.save()
				
			start_date = start_date + timedelta(days=1)
	
	#return JsonResponse(schedule)