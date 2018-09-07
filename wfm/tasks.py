# -*- coding: utf-8 -*-
"""
Created on Wed Nov 08 07:42:54 2017

@author: emota
"""
from __future__ import unicode_literals


from wfm.models import *
from django.contrib.auth.models import User
from datetime import timedelta, datetime, date
from django.db import connection
import pytz
import sys
import json
from background_task import background
from django.db.models import Q

def last_day_of_month(any_day):
	'''
	Calculate the last day of the month for the month in the given date
	Precondition: Get the date in datetime format
	Postcondition: Reutnr the last day of the monht from the date provided
	'''
	next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
	return next_month - timedelta(days=next_month.day)

@background(schedule=1)
def runsaveShiftBreaks():
	'''
	Read the job specification from the server
	Schedule all the shifts for the agents in the job record
	Schedule breaks and lunch based on SLA
	Precondition: Job is in queue status and no shifts were saved in the schedule
	Postcondition: Job is changed to queue completed and shifts are saved in the schedule. As well breaks are saved and scheduled optimized.
	'''
	#print("running shifts")
	st = Job_Status.objects.get(name="Queued")
	sr = Job_Status.objects.get(name="Running")
	sts = Job_Status.objects.get(name="Success")
	stf = Job_Status.objects.get(name="Failed")
	j = Job.objects.filter(status = st).filter(job_type = "Insert_Shifts_&_Breaks")

	for jb in j:
		jb.status = sr
		jb.save()

		#print("Starting job")
		l_t = Log_Type.objects.get(name = "Update_Job")
		log_info = {"id": str(jb.id), "status": str(jb.status)}
		l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
		l.save()

		sDate = jb.from_date
		eDate = jb.to_date + timedelta(days=1)
		cUser = jb.agents
		aUser = jb.actioned_by
		aUser = aUser.username



		try:
			if int(cUser) == 0:
				agents = User.objects.filter(groups__name = 'Agent')
				for agent in agents:
 					#print(agent)
					saveShifts(sDate, eDate, agent.username, aUser)
					#print("get breaks")
					saveBreaks(sDate, eDate, agent.username, aUser)
			else:
				cUser = User.objects.get(pk = cUser)
				cUser = cUser.username

				saveShifts(sDate, eDate, cUser, aUser)
				saveBreaks(sDate, eDate, cUser, aUser)
			jb.status = sts
			jb.save()
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
		except Exception as e:
			jb.status = stf
			jb.save()
			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()

		#print(sDate)
		#print(eDate)
		calculateSLA(sDate, eDate)

@background(schedule=1)
def runsaveShift():
	'''
	Schedule shifts for all agents based on consitions saved
	Precondition: No shifts saved.
	Postcondition: Save shifts for the agent based on the conditions set
	'''

	st = Job_Status.objects.get(name="Queued")
	sr = Job_Status.objects.get(name="Running")
	sts = Job_Status.objects.get(name="Success")
	stf = Job_Status.objects.get(name="Failed")
	j = Job.objects.filter(status = st).filter(job_type = "Insert_Shifts")

	for jb in j:
		jb.status = sr
		jb.save()

		l_t = Log_Type.objects.get(name = "Update_Job")
		log_info = {"id": str(jb.id), "status": str(jb.status)}
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
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
			calculateSLA(sDate, eDate)
		except:
			jb.status = stf
			jb.save()

			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()



@background(schedule=1)
def runsaveMeetings():
	'''
	Schedule meetings based on the SLA and group settings in the UI
	Precondition: No meeting scheduled or saved and the satus of the job as queued
	Poscondition: Meeting schedule, also returns any agents that were not able to be schedule
	'''
	st = Job_Status.objects.get(name="Queued")
	sr = Job_Status.objects.get(name="Running")
	sts = Job_Status.objects.get(name="Success")
	stf = Job_Status.objects.get(name="Failed")
	j = Job.objects.filter(status = st).filter(job_type = "Schedule_a_Meeting")

	for jb in j:
		jb.status = sr
		jb.save()

		l_t = Log_Type.objects.get(name = "Update_Job")
		log_info = {"id": str(jb.id), "status": str(jb.status)}
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
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()
			calculateSLA(sDate, eDate)
		except:
			jb.status = stf
			jb.save()

			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()


def saveShifts(sDate, eDate, cUser, aUser):
	print("saving shifts")
	user = User.objects.get(username = cUser)
	auser = User.objects.get(username = aUser)
	profile = Profile.objects.get(user = user)
	#print(user)
	#start = date.today()
	#end = last_day_of_month(date.today())
	start = sDate.date()
	end = eDate.date()

	shifts = Shift.objects.filter(user=profile).filter(valid_from__lte=end).filter(valid_to__gte=start)

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

		#print(s.day_model.time_zone)
		tzo = pytz.timezone(s.day_model.time_zone)

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
			#print(start_format)
			end_format = start_date + timedelta(days=int(s.day_model.day_end_diff))
			end_format = end_format.strftime("%Y-%m-%d")
			#print(start_format)
			#print(end_format)
			if working_days[dayName]:
				#print(dayName)
				try:
					stDate = tzo.localize(datetime.strptime(start_format + " " + day_start, '%Y-%m-%d %H:%M:%S'))
					etDate = tzo.localize(datetime.strptime(end_format + " " + day_end, '%Y-%m-%d %H:%M:%S'))
					sh_f = Shift_Sequence.objects.filter(start_date_time__gte = stDate).filter(start_date_time__lte = etDate).filter(user = profile)

					for sh1 in sh_f:
						sh1.delete()
						l_t = Log_Type.objects.get(name = "Remove_Shift_Sequence")
						log_info = {"user": str(profile), "start_date_time": str(stDate), "start_diff": str(s.day_model.day_start_diff), "end_date_time": str(etDate), "end_diff": str(s.day_model.day_end_diff), "actioned_by": str(auser)}
						l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
						l.save()

					sh = Shift_Sequence(user = profile, start_date_time = stDate, start_diff = int(s.day_model.day_start_diff), end_date_time = etDate, end_diff = int(s.day_model.day_end_diff), actioned_by = auser)
					sh.save()

					l_t = Log_Type.objects.get(name = "Add_Shift_Sequence")
					log_info = {"user": str(profile), "start_date_time": str(stDate), "start_diff": str(s.day_model.day_start_diff), "end_date_time": str(etDate), "end_diff": str(s.day_model.day_end_diff), "actioned_by": str(auser)}
					l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
					l.save()
				except Exception as e:
					print("Unexpected error:", str(e))
					pass
					#return response
			start_date = start_date + timedelta(days=1)
			#print(start_date)
	#print("running SLA")


def calculateSLA(sDate, eDate):
	'''
	Based on the shifts scheduled, SLA is recalculated
	Precondition: SLA based on the previous existing shifts
	Postcodnition: SLA recalculated after new shifts have been saved
	'''
	#print("Starting SLA calculation")
	#print(sDate)
	start = sDate.date()
	end = eDate.date()

	start_format = start.strftime("%Y-%m-%d")
	end_format = end.strftime("%Y-%m-%d")


	shifts = Shift_Sequence.objects.filter(start_date_time__date__gte = start_format).filter(start_date_time__date__lte = end_format)
	#print(shifts.query)
	with connection.cursor() as cur:
		cur.execute("update forecast_call_forecast set actual_agents_scheduled = 0 where date(`date`) >= %s and date(`date`) <= %s", (start_format, end_format))

	#print(len(shifts))
	for s in shifts:
		user_profile = s.user
		ex_list = Shift_Exception.objects.filter(shift_sequence = s)

		skills = user_profile.skill_level.all()
		#print(len(ex_list))
		ski = []
		for sk in skills:
			sk_f = sk.skill.name
			if "Phone" in sk_f:
				sk_f = sk_f.replace(" - Phone","")
			else:
				continue

			if sk_f != "English":
				ski.insert(0, sk_f)
			else:
				ski.append(sk_f)

		if len(ski) == 0:
			#print(user_profile)
			continue

		ratio = 1.0/(len(ski)*1.0)

		for sk in ski:

			start_d = s.start_date_time
			end_d = s.end_date_time

			start_d_f = start_d.strftime("%Y-%m-%d %H:%M:%S")
			end_d_f = end_d - timedelta(minutes=15)
			end_d_f = end_d_f.strftime("%Y-%m-%d %H:%M:%S")
			#print(ratio, sk)
			with connection.cursor() as cur:
				cur.execute("UPDATE `eve`.`forecast_call_forecast` SET `actual_agents_scheduled`= (`actual_agents_scheduled` + %s)  WHERE `date` >= %s and `date` <= %s and queue = %s", (ratio, start_d_f,  end_d_f, sk) )

			for ex in ex_list:
				start_d_f = ex.start_date_time.strftime("%Y-%m-%d %H:%M:%S")
				end_d_f = ex.end_date_time - timedelta(minutes=15)
				end_d_f = end_d_f.strftime("%Y-%m-%d %H:%M:%S")
				with connection.cursor() as cur:
					cur.execute("UPDATE `eve`.`forecast_call_forecast` SET `actual_agents_scheduled`= (`actual_agents_scheduled` - %s)  WHERE `date` >= %s and `date` <= %s and queue = %s", (ratio, start_d_f,  end_d_f, sk) )

@background(schedule=1)
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
		log_info = {"id": str(jb.id), "status": str(jb.status)}
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
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()

		except:
			jb.status = stf
			jb.save()

			l_t = Log_Type.objects.get(name = "Update_Job")
			log_info = {"id": str(jb.id), "status": str(jb.status)}
			l = Log(created_by = jb.actioned_by, log_type = l_t, log_info = json.dumps(log_info))
			l.save()

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

	l_t = Log_Type.objects.get(name = "Add_Shift_Exception")
	log_info = {"user": str(profile), "shift_sequence": str(s), "event": str(e), "start_date_time": str(bestTime), "start_diff": str(start_dif), "end_date_time": str(meetingTime_end), "end_diff": str(end_dif), "actioned_by": str(auser), "status": str(1)}
	l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
	l.save()

	cur.close()
	calculateSLA(sDate, eDate)

def saveBreaks(sDate, eDate, cUser, aUser):
	#print("Running adding break and lunches")
	cur = connection.cursor()

	cuuser = User.objects.get(username = cUser)
	auser = User.objects.get(username = aUser)
	profile = Profile.objects.get(user = cuuser)

	#print("Getting Breaks")
	#start = date.today()
	#end = last_day_of_month(date.today())


	shifts = Shift_Sequence.objects.filter(user=profile)
	shifts = shifts.filter(start_date_time__gte=sDate)
	shifts = shifts.filter(start_date_time__lte=eDate)


	#print(shifts.query)
	#print(len(shifts))
	print("evaluate each shift")
	i = 1
	for s in shifts:
		#print(i)
		i += 1
		#print("get skills")
		user_profile = s.user

		skills = user_profile.skill_level.all()
		#print(skills.query)

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

		#print(ski)
		#print(s)

		business_day = s.start_date_time
		business_day_end = s.end_date_time

		b_date = business_day.date()
		b_date_format = b_date.strftime("%Y-%m-%d")

		bestTimeBreak1 = None
		bestTimeBreak2 = None
		bestTimeLunch = None

		duration_Break1 = None
		duration_Break2 = None
		duration_Lunch = None

		shift_diff = business_day_end - business_day
		shift_diff_days = shift_diff.total_seconds()/60/60
		print(shift_diff_days)
		if shift_diff_days < 3:
			continue

		elif shift_diff_days < 5:
			b_time_start = business_day + timedelta(minutes=120)
			b_time_end = business_day_end - timedelta(minutes=90)
			duration_Break1 = 15
			bestTimeBreak1 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Break1, profile)
			print(bestTimeBreak1)

		elif shift_diff_days < 6:
			b_time_start = business_day + timedelta(minutes=120)
			b_time_end = business_day_end - timedelta(minutes=120)
			duration_Lunch = 30
			bestTimeLunch = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Lunch, profile)
			print(bestTimeLunch)

		elif shift_diff_days < 7:
			b_time_start = business_day + timedelta(minutes=120)
			b_time_end = business_day + timedelta(minutes=180)
			duration_Break1 = 15
			bestTimeBreak1 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Break1, profile)
			print(bestTimeBreak1)

			b_time_start = bestTimeBreak1 + timedelta(minutes=75)
			b_time_end = business_day_end - timedelta(minutes=120)
			duration_Lunch = 30
			bestTimeLunch = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Lunch, profile)
			print(bestTimeLunch)

		elif shift_diff_days < 10:
			b_time_start = business_day + timedelta(minutes=90)
			b_time_end = business_day + timedelta(minutes=150)
			duration_Break1 = 15
			bestTimeBreak1 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Break1, profile)
			print(bestTimeBreak1)

			b_time_start = bestTimeBreak1 + timedelta(minutes=105)
			b_time_end = business_day + timedelta(minutes=300)
			duration_Lunch = 30
			bestTimeLunch = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Lunch, profile)
			print(bestTimeLunch)

			b_time_start = bestTimeLunch + timedelta(minutes=120)
			b_time_end = business_day_end - timedelta(minutes=60)
			duration_Break2 = 15
			bestTimeBreak2 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Break2, profile)
			print(bestTimeBreak2)

		elif shift_diff_days < 11:

			if business_day.hour > 7:
				print("day")
				print(business_day)
				print(business_day_end)
				duration_Break1 = 15
				bestTimeBreak1 = business_day + timedelta(minutes=150)

				duration_Lunch = 30
				bestTimeLunch = business_day + timedelta(minutes=300)

				b_time_start = bestTimeLunch + timedelta(minutes=150)
				b_time_end = bestTimeLunch + timedelta(minutes=210)
				duration_Break2 = 15

				bestTimeBreak2 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Break2, profile)
				print(bestTimeBreak2)
			else:
				print("nigth 10 hours")
				b_time_start = business_day + timedelta(minutes=180)
				b_time_end = business_day + timedelta(minutes=270)
				duration_Break1 = 30
				bestTimeBreak1 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Break1, profile)
				print(bestTimeBreak1)
				duration_Lunch = 30
				bestTimeLunch = bestTimeBreak1 + timedelta(minutes=180)

		elif shift_diff_days <= 12:
			b_time_start = business_day + timedelta(minutes=90)
			b_time_end = business_day + timedelta(minutes=150)
			duration_Break1 = 15
			bestTimeBreak1 = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Break1, profile)
			print(bestTimeBreak1)

			b_time_start = bestTimeBreak1 + timedelta(minutes=120)
			b_time_end = bestTimeBreak1 + timedelta(minutes=150)
			duration_Lunch = 30
			bestTimeLunch = findBestTime(ski, b_date_format, b_time_start, b_time_end, duration_Lunch, profile)
			print(bestTimeLunch)
			duration_Break2 = 30
			bestTimeBreak2 = bestTimeLunch + timedelta(minutes=210)

		ev_b = Event.objects.get(name="Break")
		ev_l = Event.objects.get(name="Lunch")


		s_ex_del_list = Shift_Exception.objects.filter(Q(shift_sequence = s) & Q(user = profile) & (Q(event__name = 'Break') | Q(event__name = 'Lunch')))

		for s_ex_1 in s_ex_del_list:
			s_ex_1.delete()

		if bestTimeBreak1:
			bestTimeBreak1_end = bestTimeBreak1 + timedelta(minutes=duration_Break1)
			start_dif = (business_day - bestTimeBreak1).days
			end_dif = (business_day - bestTimeBreak1_end).days
			try:
				s_ex = Shift_Exception(user = profile, shift_sequence = s, event = ev_b, start_date_time = bestTimeBreak1, start_diff = start_dif, end_date_time = bestTimeBreak1_end, end_diff = end_dif, actioned_by = auser, status = 1)
				s_ex.save()
				print(s_ex)
			except Exception as e:
				print(e)
				print("Break 1 Time")

			try:
				l_t = Log_Type.objects.get(name = "Add_Shift_Exception")
				log_info = {"user": str(profile), "shift_sequence": str(s), "event": str(ev_b), "start_date_time": str(bestTimeBreak1), "start_diff": str(start_dif), "end_date_time": str(bestTimeBreak1_end), "end_diff": str(end_dif), "actioned_by": str(auser.profile), "status": str(1)}
				l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
				l.save()
			except Exception as e:
				print(e)
				print("Log break 1 time")

		if bestTimeBreak2:
			print("break 2 to be saved")
			try:
				bestTimeBreak2_end = bestTimeBreak2 + timedelta(minutes=duration_Break2)
				start_dif = (business_day - bestTimeBreak2).days
				end_dif = (business_day - bestTimeBreak2_end).days
				#print(business_day, bestTimeBreak2)
				s_ex_2 = Shift_Exception(user = profile, shift_sequence = s, event = ev_b, start_date_time = bestTimeBreak2, start_diff = start_dif, end_date_time = bestTimeBreak2_end, end_diff = end_dif, actioned_by = auser, status = 1)
				s_ex_2.save()
				print(s_ex_2)
			except Exception as e:
				print(e)
				print("Break 2 time")
			print("break 2 saved")
			try:
				l_t = Log_Type.objects.get(name = "Add_Shift_Exception")
				log_info = {"user": str(profile), "shift_sequence": str(s), "event": str(ev_b), "start_date_time": str(bestTimeBreak1), "start_diff": str(start_dif), "end_date_time": str(bestTimeBreak1_end), "end_diff": str(end_dif), "actioned_by": str(auser.profile), "status": str(1)}
				l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
				l.save()

			except Exception as e:
				print(e)
				print("Log break 2 time")

		if bestTimeLunch:
			print("lunch to be saved")
			try:
				bestTimeLunch_end = bestTimeLunch + timedelta(minutes=30)

				start_dif = (business_day - bestTimeLunch).days
				end_dif = (business_day - bestTimeLunch_end).days

				s_ex_l = Shift_Exception(user = profile, shift_sequence = s, event = ev_l, start_date_time = bestTimeLunch, start_diff = start_dif, end_date_time = bestTimeLunch_end, end_diff = end_dif, actioned_by = auser, status = 1)
				s_ex_l.save()
				print(s_ex_l)
			except Exception as e:
				print(e)
				print("Lunch time")

			try:
				l_t = Log_Type.objects.get(name = "Add_Shift_Exception")
				log_info = {"user": str(profile), "shift_sequence": str(s), "event": str(ev_b), "start_date_time": str(bestTimeBreak1), "start_diff": str(start_dif), "end_date_time": str(bestTimeBreak1_end), "end_diff": str(end_dif), "actioned_by": str(auser.profile), "status": str(1)}
				l = Log(created_by = auser, log_type = l_t, log_info = json.dumps(log_info))
				l.save()
			except Exception as e:
				print(e)
				print("Log Lunch time")

	print("breaks all saved")
	cur.close()
	try:
		calculateSLA(sDate, eDate)
	except Exception as e:
		print(e)
		print("calculation of SLA")

def findBestTime(ski, b_date_format, b_time_start, b_time_end, duration, pro, override=False):
	print("trying to connect")
	c = connection.cursor()
	print("Trying to find time")
	duration = int(duration)

	b_time_start_format = b_time_start.strftime("%Y-%m-%d %H:%M:%S")
	print(b_time_start_format)
	#b_time_end_format = b_time_end - timedelta(minutes = duration)
	b_time_end_format = b_time_end.strftime("%Y-%m-%d %H:%M:%S")
	print(b_time_end_format)
	intervals = duration / 15
	print(intervals)
	diff = {}
	print("finding the best time")
	for sk in ski:
		#c.execute("SELECT `date`, (agents_required - actual_agents_scheduled) as d from forecast_call_forecast where `date` >= %s and `date` < %s and queue = %s", (b_time_start_format, b_time_end_format, sk))
		c.execute("SELECT `date`, actual_agents_scheduled as d from forecast_call_forecast where `date` >= %s and `date` <= %s and queue = %s", (b_time_start_format, b_time_end_format, sk))
		results = c.fetchall()
		print(len(results))
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
					s_e = Shift_Exception.objects.filter(Q(start_date_time__lte = date_out) & Q(end_date_time__gte = date_in) & Q(user=pro) & (Q(event__group__name = 'Meeting') | Q(event__group__name = 'Timeoff')))
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
	print(diff)
	besttime = None
	lowestAgents = None
	for k, value in diff.items():
		if value > lowestAgents or not lowestAgents:
			lowestAgents = value
			besttime = k
	print(besttime)
	c.close()
	#tzo = pytz.timezone("UTC")
	#besttime = tzo.localize(besttime)
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
		c.execute("SELECT `date`, actual_agents_scheduled as d from forecast_call_forecast where `date` >= %s and `date` < %s and queue = %s", (b_time_start_format, b_time_end_format, sk))
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
	lowestAgents = None

	for k, value in diff.items():
		if value > lowestAgents or not lowestAgents:
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
	b_time_end_format = b_time_end_format.strftime("%Y-%m-%d %H:%M:%S")

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
