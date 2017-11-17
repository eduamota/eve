# -*- coding: utf-8 -*-
"""
Created on Wed Nov 08 07:42:54 2017

@author: emota
"""
from __future__ import unicode_literals


from wfm.models import Shift, Profile, Shift_Exception, Job, Shift_Sequence, Job_Status, Event
from django.contrib.auth.models import User
from datetime import timedelta, datetime, date
from celery import shared_task
from django.db import connection
import pytz

def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
	return next_month - timedelta(days=next_month.day)

@shared_task
def runsaveShiftBreaks():
	
	st = Job_Status.objects.get(name="Queued")
	sr = Job_Status.objects.get(name="Running")
	sts = Job_Status.objects.get(name="Success")
	stf = Job_Status.objects.get(name="Failed")
	j = Job.objects.filter(status = st).filter(job_type = "Insert_Shifts_&_Breaks")
	
	for jb in j:
		jb.status = sr
		jb.save()
		sDate = jb.from_date
		eDate = jb.to_date
		cUser = jb.agents
		aUser = jb.actioned_by
		aUser = aUser.username
		
		try:
			if int(cUser) == 0:
				agents = User.objects.filter(groups__name = 'Agent')
				for agent in agents:
					saveShifts(sDate, eDate, agent.username, aUser)
					saveBreaks(sDate, eDate, agent.username, aUser)
			else:
				cUser = User.objects.get(pk = cUser)
				cUser = cUser.username
			
				saveShifts(sDate, eDate, cUser, aUser)
				saveBreaks(sDate, eDate, cUser, aUser)
			jb.status = sts
			jb.save()
		except:
			jb.status = stf
			jb.save()
	calculateSLA(sDate, eDate)

@shared_task
def runsaveShift():		
	
	st = Job_Status.objects.get(name="Queued")
	sr = Job_Status.objects.get(name="Running")
	sts = Job_Status.objects.get(name="Success")
	stf = Job_Status.objects.get(name="Failed")
	j = Job.objects.filter(status = st).filter(job_type = "Insert_Shifts")
	
	for jb in j:
		jb.status = sr
		jb.save()
		sDate = jb.from_date
		eDate = jb.to_date
		cUser = jb.agents
		aUser = jb.actioned_by
		aUser = aUser.username
		
		try:
			if int(cUser) == 0:
				agents = User.objects.filter(groups__name = 'Agent')
				for agent in agents:
					saveShifts(sDate, eDate, agent.username, aUser)
			else:
				cUser = User.objects.get(pk = cUser)
				cUser = cUser.username
			
				saveShifts(sDate, eDate, cUser, aUser)
			jb.status = sts
			jb.save()
		except:
			jb.status = stf
			jb.save()
			
	calculateSLA(sDate, eDate)
			
def saveShifts(sDate, eDate, cUser, aUser):
	#print("saving shifts")
	user = User.objects.get(username = cUser)
	auser = User.objects.get(username = aUser)
	profile = Profile.objects.get(user = user)
	
	#start = date.today()
	#end = last_day_of_month(date.today())
	start = sDate.date()
	end = eDate.date()
	
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
			
			end_format = start_date + timedelta(days=int(s.day_model.day_end_diff))
			end_format = end_format.strftime("%Y-%m-%d")
			
			if working_days[dayName]:
				try:
					stDate = datetime.strptime(start_format + " " + day_start, '%Y-%m-%d %H:%M:%S')
					etDate = datetime.strptime(end_format + " " + day_end, '%Y-%m-%d %H:%M:%S')
					sh_f = Shift_Sequence.objects.filter(start_date_time__date = start_format).filter(user = profile)
					for sh1 in sh_f:
						sh1.delete()
					sh = Shift_Sequence(user = profile, start_date_time = stDate, start_diff = int(s.day_model.day_start_diff), end_date_time = etDate, end_diff = int(s.day_model.day_end_diff), actioned_by = auser)
					sh.save()			
				except:
					pass
					#return response
			start_date = start_date + timedelta(days=1)
	#print("running SLA")
	
			
def calculateSLA(sDate, eDate):
	
	start = sDate.date()
	end = eDate.date()

	start_format = start.strftime("%Y-%m-%d")
	end_format = end.strftime("%Y-%m-%d")


	shifts = Shift_Sequence.objects.filter(start_date_time__date__gte = start_format).filter(start_date_time__date__lte = end_format)
	
	cur = connection.cursor()
	cur.execute("update forecast_call_forecast set actual_agents_scheduled = 0 where date(`date`) >= %s and date(`date`) <= %s", (start_format, end_format))
	
	for s in shifts:
		user_profile = s.user
		
		ex_list = Shift_Exception.objects.filter(shift_sequence = s)
		
		skills = user_profile.skill.all()

		ski = []
		for sk in skills:
			sk_f = sk.name
			if "Phone" in sk_f:
				sk_f = sk_f.replace(" - Phone","")
			else:
				continue
			
			if sk_f != "English":
				ski.insert(0, sk_f)
			else:
				ski.append(sk_f)
		
		ratio = 1.0/(len(ski)*1.0)		

		for sk in ski:
			
			start_d = s.start_date_time
			end_d = s.end_date_time
			
			start_d_f = start_d.strftime("%Y-%m-%d %H:%M:%S")								
			end_d_f = end_d - timedelta(minutes=15)
			end_d_f = end_d_f.strftime("%Y-%m-%d %H:%M:%S")	
			
			cur.execute("UPDATE `eve`.`forecast_call_forecast` SET `actual_agents_scheduled`= (`actual_agents_scheduled` + %s)  WHERE `date` >= %s and `date` <= %s and queue = %s", (ratio, start_d_f,  end_d_f, sk) )
			
			for ex in ex_list:
				start_d_f = ex.start_date_time.strftime("%Y-%m-%d %H:%M:%S")
				end_d_f = ex.end_date_time - timedelta(minutes=15)
				end_d_f = end_d_f.strftime("%Y-%m-%d %H:%M:%S")
				cur.execute("UPDATE `eve`.`forecast_call_forecast` SET `actual_agents_scheduled`= (`actual_agents_scheduled` - %s)  WHERE `date` >= %s and `date` <= %s and queue = %s", (ratio, start_d_f,  end_d_f, sk) )
				
	cur.close()

@shared_task
def runsaveBreaks():		
	
	st = Job_Status.objects.get(name="Queued")
	sr = Job_Status.objects.get(name="Running")
	sts = Job_Status.objects.get(name="Success")
	stf = Job_Status.objects.get(name="Failed")
	j = Job.objects.filter(status = st).filter(job_type = "Add_Breaks_and_Lunches")
	
	for jb in j:
		jb.status = sr
		jb.save()
		sDate = jb.from_date
		eDate = jb.to_date
		cUser = jb.agents
		aUser = jb.actioned_by
		aUser = aUser.username
		
		try:
			if int(cUser) == 0:
				agents = User.objects.filter(groups__name = 'Agent')
				for agent in agents:
					saveBreaks(sDate, eDate, agent.username, aUser)
			else:
				cUser = User.objects.get(pk = cUser)
				cUser = cUser.username
			
				saveBreaks(sDate, eDate, cUser, aUser)
			jb.status = sts
			jb.save()
		except:
			jb.status = stf
			jb.save()
			
	calculateSLA(sDate, eDate)
	
def saveBreaks(sDate, eDate, cUser, aUser):
	
	cur = connection.cursor()
		
	cuuser = User.objects.get(username = cUser)
	auser = User.objects.get(username = aUser)
	profile = Profile.objects.get(user = cuuser)
	
	#start = date.today()
	#end = last_day_of_month(date.today())
	start = sDate.date()
	end = eDate.date()
	
	shifts = Shift_Sequence.objects.filter(user=profile)
	shifts = shifts.filter(start_date_time__date__gte=start)
	shifts = shifts.filter(start_date_time__date__lte=end)
	
	#print shifts.query
	#print len(shifts)
	for s in shifts:
		
		user_profile = s.user
		
		skills = user_profile.skill.all()

		ski = []
		for sk in skills:
			sk_f = sk.name
			if "Phone" in sk_f:
				sk_f = sk_f.replace(" - Phone","")
			else:
				continue
			
			if sk_f != "English":
				ski.insert(0, sk_f)
			else:
				ski.append(sk_f)
				
		business_day = s.start_date_time		
		
		b_date = business_day.date()
		b_date_format = b_date.strftime("%Y-%m-%d")
		
		b_time_start = business_day + timedelta(minutes=30)		
		b_time_end = business_day + timedelta(minutes=150)
		
		duration = 15

		bestTimeBreak1 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration)
		
		b_time_start = business_day + timedelta(minutes=210)		
		b_time_end = business_day + timedelta(minutes=300)
		
		duration = 30

		bestTimeLunch = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration)
		
		b_time_start = business_day + timedelta(minutes=360)		
		b_time_end = business_day + timedelta(minutes=435)
		
		duration = 15
		
		bestTimeBreak2 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration)
		
		ev_b = Event.objects.get(name="Break")
		ev_l = Event.objects.get(name="Lunch")
		
		
		s_ex_del_list = Shift_Exception.objects.filter(shift_sequence = s).filter(user = profile)
		for s_ex_1 in s_ex_del_list:
			s_ex_1.delete()

		bestTimeBreak1_end = bestTimeBreak1 + timedelta(minutes=15)
		start_dif = business_day.day - bestTimeBreak1.day
		end_dif = business_day.day - bestTimeBreak1_end.day
		s_ex = Shift_Exception(user = profile, shift_sequence = s, event = ev_b, start_date_time = bestTimeBreak1, start_diff = start_dif, end_date_time = bestTimeBreak1_end, end_diff = end_dif, actioned_by = auser, approved = True)
		s_ex.save()
		
		bestTimeBreak2_end = bestTimeBreak2 + timedelta(minutes=15)
		start_dif = business_day.day - bestTimeBreak2.day
		end_dif = business_day.day - bestTimeBreak2_end.day
		s_ex_2 = Shift_Exception(user = profile, shift_sequence = s, event = ev_b, start_date_time = bestTimeBreak2, start_diff = start_dif, end_date_time = bestTimeBreak2_end, end_diff = end_dif, actioned_by = auser, approved = True)
		s_ex_2.save()
		
		bestTimeLunch_end = bestTimeLunch + timedelta(minutes=30)
		start_dif = business_day.day - bestTimeLunch.day
		end_dif = business_day.day - bestTimeLunch_end.day
		s_ex_l = Shift_Exception(user = profile, shift_sequence = s, event = ev_l, start_date_time = bestTimeLunch, start_diff = start_dif, end_date_time = bestTimeLunch_end, end_diff = end_dif, actioned_by = auser, approved = True)
		s_ex_l.save()
		
	cur.close()
		
		
def findBestTime(ski, b_date_format, b_time_start, b_time_end, duration):
	c = connection.cursor()
	
	b_time_start_format = b_time_start.strftime("%Y-%m-%d %H:%M:%S")
	
	b_time_end_format = b_time_end + timedelta(minutes = (duration-15))
	b_time_end_format = b_time_end.strftime("%Y-%m-%d %H:%M:%S")
	
	intervals = duration / 15

	diff = {}
	
	for sk in ski:
		c.execute("SELECT `date`, (agents_required - actual_agents_scheduled) as d from forecast_call_forecast where `date` >= %s and `date` <= %s and queue = %s", (b_time_start_format, b_time_end_format, sk))
		results = c.fetchall()
		
		for r in results:
			if r[0] not in diff:
				diff[r[0]] = 0
				
		for r in results:
			i = 0
			total = 0
			while i < intervals:
				m = 15 * i
				date_in = r[0] + timedelta(minutes=m)
				if date_in in diff:
					total = total + float(r[1])
				else:
					if r[0] in diff:
						print date_in
						print r[0]
						del diff[r[0]]
				i += 1
				
			if r[0] in diff:
				diff[r[0]] = diff[r[0]] + total
	
	
		
	besttime = ""
	lowestAgents = -1

	for k, value in diff.items():
		if value < lowestAgents or lowestAgents == -1:
			lowestAgents = value
			besttime = k
	c.close()
	
	return besttime 
				
		
		
		
		
	
	
	
	