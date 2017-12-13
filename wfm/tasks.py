# -*- coding: utf-8 -*-
"""
Created on Wed Nov 08 07:42:54 2017

@author: emota
"""
from __future__ import unicode_literals


from wfm.models import Shift, Profile, Shift_Exception, Job, Shift_Sequence, Job_Status, Event, Log, Log_Type
from django.contrib.auth.models import User
from datetime import timedelta, datetime, date
from celery import shared_task
from django.db import connection
import pytz
import sys
import json
import collections

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

		l_t = Log_Type.objects.get(name = "Update_Job")
		log_info = {"id": jb.id, "status":jb.status}
		l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
		l.save()		
		
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
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
		except:
			jb.status = stf
			jb.save()
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
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

		l_t = Log_Type.objects.get(name = "Update_Job")
		log_info = {"id": jb.id, "status":jb.status}
		l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
		l.save()		
		
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
			
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
		except:
			jb.status = stf
			jb.save()
			
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
			
	calculateSLA(sDate, eDate)
	
@shared_task
def runsaveMeetings():
	
	st = Job_Status.objects.get(name="Queued")
	sr = Job_Status.objects.get(name="Running")
	sts = Job_Status.objects.get(name="Success")
	stf = Job_Status.objects.get(name="Failed")
	j = Job.objects.filter(status = st).filter(job_type = "Schedule_a_Meeting")
	
	for jb in j:
		jb.status = sr
		jb.save()

		l_t = Log_Type.objects.get(name = "Update_Job")
		log_info = {"id": jb.id, "status":jb.status}
		l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
		l.save()		
		
		sDate = jb.from_date
		eDate = jb.to_date
		cUser = jb.agents
		aUser = jb.actioned_by
		aUser = aUser.username
		
		try:
			if int(cUser) == 0:
				agents = User.objects.filter(groups__name = 'Agent')
				for agent in agents:
					saveMeetings(sDate, eDate, agent.username, aUser, jb.parameters)
			else:
				cUser = User.objects.get(pk = cUser)
				cUser = cUser.username
			
				saveMeetings(sDate, eDate, cUser, aUser, jb.parameters)
			jb.status = sts
			jb.save()
			
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
		except:
			jb.status = stf
			jb.save()
			
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
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

	tzo = pytz.timezone("UTC")
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
					stDate = tzo.localize(datetime.strptime(start_format + " " + day_start, '%Y-%m-%d %H:%M:%S'))
					etDate = tzo.localize(datetime.strptime(end_format + " " + day_end, '%Y-%m-%d %H:%M:%S'))

					sh_f = Shift_Sequence.objects.filter(start_date_time__date = start_format).filter(user = profile)
					for sh1 in sh_f:
						sh1.delete()
					
					sh = Shift_Sequence(user = profile, start_date_time = stDate, start_diff = int(s.day_model.day_start_diff), end_date_time = etDate, end_diff = int(s.day_model.day_end_diff), actioned_by = auser)
					sh.save()
					
					l_t = Log_Type.objects.get(name = "Add_Shift_Sequence")
					log_info = {"user": profile, "start_date_time": stDate, "start_diff": str(s.day_model.day_start_diff), "end_date_time": etDate, "end_diff": str(s.day_model.day_end_diff), "actioned_by": auser}
					l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
					l.save()
				except:
					print "Unexpected error:", sys.exc_info()[0]
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
		
		l_t = Log_Type.objects.get(name = "Update_Job")
		log_info = {"id": jb.id, "status":jb.status}
		l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
		l.save()	
		
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
			
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()	
		except:
			jb.status = stf
			jb.save()
			
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": jb.id, "status":jb.status}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()	
			
	calculateSLA(sDate, eDate)
	
def saveMeetings(sDate, eDate, cUser, aUser, parameters):
	
	cur = connection.cursor()
		
	cuuser = User.objects.get(username = cUser)
	auser = User.objects.get(username = aUser)
	profile = Profile.objects.get(user = cuuser)
	
	#start = date.today()
	#end = last_day_of_month(date.today())
	start = sDate.date()
	end = eDate.date()
	
	skills = profile.skill.all()

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
	
	
	p_j = json.loads(parameters)
	
	start_date = sDate.strftime("%Y-%m-%d")
	start_time = sDate.strftime("%H:%M:%S")
	end_time = eDate.strftime("%H:%M:%S")
	duration = p_j['duration']
	notes = p_j['notes']
	ev = p_j['event']
	override = p_j['override']
	
	shifts = Shift_Sequence.objects.filter(user=profile)
	shifts = shifts.filter(start_date_time__date__gte=sDate)
	shifts = shifts.filter(start_date_time__date__lte=eDate)
	
	bestTime = ""
	
	bestTime = ""
	lowest = -1
	for s in shifts:

		meetingTime, agents = findBestTimeMultiple(ski, s.start_date_time.date(), s.start_date_time, s.end_date_time, duration, profile, override)
		
		if agents < lowest or lowest == -1:
			bestTime = meetingTime
			lowest = agents
	
	
	start = bestTime.date()
	
	
	meetingTime_end = bestTime + timedelta(minutes=int(duration))
	
	s = Shift_Sequence.objects.get(user=profile, start_date_time__date = start)
	
	#print s.pk
	start_dif = 0
	end_dif = 0
	
	e = Event.objects.get(name=ev)
			
	s_ex_l = Shift_Exception(user = profile, shift_sequence = s, event = e, start_date_time = bestTime, start_diff = start_dif, end_date_time = meetingTime_end, end_diff = end_dif, actioned_by = auser, status = 1)
	
	s_ex_l.save()
	
	l_t = Log_Type.objects.get(name = "Add_Shift_Exceptionb")
	log_info = {"user": profile, "shift_sequence": s, "event": e, "start_date_time": bestTime, "start_diff": start_dif, "end_date_time": meetingTime_end, "end_diff": end_dif, "actioned_by": auser, "status": 1}
	l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
	l.save()	
		
	cur.close()
	
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

		bestTimeBreak1 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration, profile)
		
		b_time_start = business_day + timedelta(minutes=210)		
		b_time_end = business_day + timedelta(minutes=300)
		
		duration = 30

		bestTimeLunch = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration, profile)
		
		b_time_start = business_day + timedelta(minutes=360)		
		b_time_end = business_day + timedelta(minutes=435)
		
		duration = 15
		
		bestTimeBreak2 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration, profile)
		
		ev_b = Event.objects.get(name="Break")
		ev_l = Event.objects.get(name="Lunch")
		
		
		s_ex_del_list = Shift_Exception.objects.filter(shift_sequence = s).filter(user = profile)
		for s_ex_1 in s_ex_del_list:
			s_ex_1.delete()

		bestTimeBreak1_end = bestTimeBreak1 + timedelta(minutes=15)
		start_dif = business_day.day - bestTimeBreak1.day
		end_dif = business_day.day - bestTimeBreak1_end.day
		s_ex = Shift_Exception(user = profile, shift_sequence = s, event = ev_b, start_date_time = bestTimeBreak1, start_diff = start_dif, end_date_time = bestTimeBreak1_end, end_diff = end_dif, actioned_by = auser, status = 1)
		s_ex.save()
		
		l_t = Log_Type.objects.get(name = "Add_Shift_Exceptionb")
		log_info = {"user": profile, "shift_sequence": s, "event": ev_b, "start_date_time": bestTimeBreak1, "start_diff": start_dif, "end_date_time": bestTimeBreak1_end, "end_diff": end_dif, "actioned_by": auser, "status": 1}
		l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
		l.save()
		
		bestTimeBreak2_end = bestTimeBreak2 + timedelta(minutes=15)
		start_dif = business_day.day - bestTimeBreak2.day
		end_dif = business_day.day - bestTimeBreak2_end.day
		s_ex_2 = Shift_Exception(user = profile, shift_sequence = s, event = ev_b, start_date_time = bestTimeBreak2, start_diff = start_dif, end_date_time = bestTimeBreak2_end, end_diff = end_dif, actioned_by = auser, status = 1)
		s_ex_2.save()
		
		l_t = Log_Type.objects.get(name = "Add_Shift_Exceptionb")
		log_info = {"user": profile, "shift_sequence": s, "event": ev_b, "start_date_time": bestTimeBreak2, "start_diff": start_dif, "end_date_time": bestTimeBreak2_end, "end_diff": end_dif, "actioned_by": auser, "status": 1}
		l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
		l.save()
		
		bestTimeLunch_end = bestTimeLunch + timedelta(minutes=30)
		start_dif = business_day.day - bestTimeLunch.day
		end_dif = business_day.day - bestTimeLunch_end.day
		s_ex_l = Shift_Exception(user = profile, shift_sequence = s, event = ev_l, start_date_time = bestTimeLunch, start_diff = start_dif, end_date_time = bestTimeLunch_end, end_diff = end_dif, actioned_by = auser, status = 1)
		s_ex_l.save()
		
		l_t = Log_Type.objects.get(name = "Add_Shift_Exceptionb")
		log_info = {"user": profile, "shift_sequence": s, "event": ev_b, "start_date_time": bestTimeLunch, "start_diff": start_dif, "end_date_time": bestTimeLunch_end, "end_diff": end_dif, "actioned_by": auser, "status": 1}
		l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
		l.save()
		
	cur.close()
		
		
def findBestTime(ski, b_date_format, b_time_start, b_time_end, duration, pro, override=False):
	c = connection.cursor()
	
	duration = int(duration)
	
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
				s_e = Shift_Exception.object.filter(start_date_time__lte = date_in).filter(end_date_time__gte = r[0]).filter(user=pro)
				if len(s_e) > 0:
					if r[0] in diff:

						del diff[r[0]]
				elif date_in in diff:
					total = total + float(r[1])
				else:
					if r[0] in diff:

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
	tzo = pytz.timezone("UTC")
	
	besttime = tzo.localize(besttime)
	return besttime 
	
def findBestTimeMultiple(ski, b_date_format, b_time_start, b_time_end, duration, pro, override=False):
	c = connection.cursor()
	
	duration = int(duration)
	
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
	tzo = pytz.timezone("UTC")
	
	besttime = tzo.localize(besttime)

	return besttime, lowestAgents

def findBestTimes(ski, b_date_format, b_time_start, b_time_end, duration):
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

						del diff[r[0]]
				i += 1
				
			if r[0] in diff:
				diff[r[0]] = diff[r[0]] + total
	
	
		
	besttimes = []
	lowestAgents = -1
	tzo = pytz.timezone("UTC")
	
	for k, value in diff.items():
		if value < lowestAgents or lowestAgents == -1:
			lowestAgents = value
			besttimes.append(tzo.localize(k))
	c.close()
	
	return besttimes.sort()			
		
		
		
		
	
	
	
	