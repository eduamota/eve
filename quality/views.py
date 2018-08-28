# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import connection, connections
from django.contrib.auth.models import User
import re
from utils.models import Profile
from clients.models import Language
from quality.models import Form, Section, Question, Evaluation, Response, Form_Overview, Form_Evaluation
import sys
from django.db.models import Q
from datetime import datetime, timedelta
import pytz
import os
import csv
from django.http import HttpResponse
from wsgiref.util import FileWrapper

# Create your views here.
#@permission_required('polls.can_vote')
@login_required()
def formAction(request, form = -1):

	#Setup variables to keep track of variables for options in page
	agents = {}
	languages = {}
	fields = {}
	dropdowns = {}
	errors = {}
	messages = []
	evaluator = request.user
	supervisor = {}

	#Run queries to retrieve the list of agents & language
	with connection.cursor() as cursor:

		cursor.execute("SELECT id, concat(first_name, ' ', last_name) as name FROM ops_system.otrs_user where email = %s", [evaluator.email,])
		result = cursor.fetchone()
		supervisor = {result[0]: result[1],}


		cursor.execute("SELECT id, concat(first_name, ' ', last_name) as name FROM ops_system.otrs_user where title like '%Customer Service Specialist' and otrs_enable = 1")
		agents_raw = cursor.fetchall()

		for agent in agents_raw:
			agents[agent[0]] = agent[1]

		cursor.execute('SELECT id, name FROM ops_system.language')
		languages_raw = cursor.fetchall()

		for language in languages_raw:
			languages[language[0]] = language[1]

	c = connection.cursor()




	#Action the form when submitted, and evaluate the form.
	if request.POST:

		for key, value in request.POST.items():
			pattern = re.compile("^([\d]+)$")

			if pattern.match(key) or key == "evalType" or key == "language" or key == "agentName":
				dropdowns[key] = value
			else:
				fields[key] = value

		if 'agentName' not in request.POST:
			errors['agentName'] = "Agent Name is required"

		if 'language' not in request.POST:
			errors['language'] = "Language is required"

		if len(request.POST['walletNumber']) == 0:
			errors['walletNumber'] = "Wallet NUmberis required"

		if len(request.POST['dateCall']) == 0:
			errors['dateCall'] = "Date of Call is required"

		if len(request.POST['typeCall']) == 0:
			errors['typeCall'] = "Program Name is required"

		if len(request.POST['recordingFile']) == 0:
			errors['recordingFile'] = "Recording File is required"

		if 'evalType' not in request.POST:
			errors['evalType'] = "Evaluation Type is required"

		if request.POST['TotalScore'] == 0:
			errors['TotalScore'] = "At least one question needs to be scored"

		if errors:
			c.close()
			return render(request, 'quality/default.html', {'errors': errors, 'supervisor': supervisor, 'agents': agents, 'languages': languages})
		else:
			#Evaluate if the form was submited vs udated
			if form == -1:
				try:
					#save the general details first
					c.execute("INSERT INTO ops_system.quality_form (agent_id, language, wallet_id, date_of_call, type_of_call, eval_id, recording_file, score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [request.POST['agentName'], request.POST['language'], request.POST['walletNumber'], request.POST['dateCall'], request.POST['typeCall'], request.POST['evalName'], request.POST['recordingFile'], request.POST['TotalScore']])

					formID = c.lastrowid

					#save each field
					for key, value in fields.items():
						c.execute("INSERT INTO ops_system.quality_responses (form_id, field_name, field_value) VALUES (%s, %s, %s)", [formID, key, value])
					#confirm form has been saved
					messages.append("<script>Materialize.toast('New record created successfully. The evaluation ID is: " + str(formID) + "', 4000, 'green');</script>")
				except:
					#send error back that there was an issue
					messages.append("<script>Materialize.toast('Error unable to save form', 4000, 'red');</script>")
			elif(int(form) > -1):
				try:
					#save the general details first
					c.execute("UPDATE ops_system.quality_form set agent_id = %s, language = %s, wallet_id = %s, date_of_call = %s, type_of_call = %s, eval_id = %s, recording_file = %s, score = %s WHERE id = %s" , [request.POST['agentName'], request.POST['language'], request.POST['walletNumber'], request.POST['dateCall'], request.POST['typeCall'], request.POST['evalName'], request.POST['recordingFile'], request.POST['TotalScore'], form])

					#save each field
					for key, value in fields.items():
						c.execute("REPLACE INTO ops_system.quality_responses (form_id, field_name, field_value) VALUES (%s, %s, %s)", [form, key, value])
					#confirm form has been saved
					messages.append("Evaluation ID " + str(form) + " has been updated.")
				except:
					#send error back that there was an issue
					errors['general'] = "Error unable to save form"
	elif int(form) > -1:
		print form
		c.execute("SELECT * FROM ops_system.quality_responses where form_id = %s", [form,])
		results = c.fetchall()

		for row in results:
			pattern = re.compile("^([\d]+)$")

			if pattern.match(row[2]) or row[2] == "evalType" or row[2] == "language" or row[2] == "agentName" or row[2] == "evalName":
				if row[2] == 'evalName':
					c.execute("SELECT id, concat(first_name, ' ', last_name) as name FROM ops_system.otrs_user where id = %s", [row[3],])
					sup = c.fetchone()
					print sup
					supervisor[sup[0]] = sup[1]

				dropdowns[row[2]] = row[3]
			else:
				fields[row[2]] = row[3]

	c.close()
	return render(request, 'quality/default.html', {'agents': agents, 'languages': languages, 'supervisor': supervisor, 'messages': messages, 'fields':fields, 'dropdowns':dropdowns})

@login_required()
def formSearch(request):
	dbFields = ["agent_id", "language", "wallet_id","date_of_call", "type_of_call", "eval_id", "recording_file", "score"]

	#Setup variables to keep track of variables for options in page
	agents = {}
	languages = {}
	fields = {}
	dropdowns = {}
	errors = {}
	messages = []
	supervisors = {}
	sections = []

	#Run queries to retrieve the list of agents & language
	with connection.cursor() as cursor:

		cursor.execute("SELECT id, concat(first_name, ' ', last_name) as name FROM ops_system.otrs_user where title like '%Customer Service Team%' and otrs_enable = 1")
		result = cursor.fetchall()

		for agent in result:
			supervisors[agent[0]] = agent[1]


		cursor.execute("SELECT id, concat(first_name, ' ', last_name) as name FROM ops_system.otrs_user where title like '%Customer Service Specialist' and otrs_enable = 1")
		agents_raw = cursor.fetchall()

		for agent in agents_raw:
			agents[agent[0]] = agent[1]

		cursor.execute('SELECT id, name FROM ops_system.language')
		languages_raw = cursor.fetchall()

		for language in languages_raw:
			languages[language[0]] = language[1]



	if request.POST:
		for key, value in request.POST.items():
			pattern = re.compile("^([\d]+)$")

			if pattern.match(key) or key == "evalType" or key == "language" or key == "agent_id" or key == "eval_id":
				dropdowns[key] = value
			else:
				fields[key] = value
		queryFilters = ""
		filters = {}
		for key, value in request.POST.items():
			filters[key] = value

		for k, v in filters.items():
			if k in dbFields and len(str(v)) > 0:
				queryFilters = queryFilters +  " " + k + "='" + v + "' and"

		queryFilters = queryFilters[:-4]
		query = "SELECT ops_system.quality_form.id, concat(o1.first_name, ' ', o1.last_name) as agent_id, l.name as language, wallet_id, date_of_call, type_of_call, concat(o2.first_name, ' ', o2.last_name) as eval_id, recording_file, score FROM ops_system.quality_form, ops_system.otrs_user o1, ops_system.otrs_user o2, ops_system.language l where agent_id = o1.id and eval_id = o2.id and language = l.id and " + queryFilters

		c = connection.cursor()

		c.execute(query)

		results = c.fetchall()
		forms = {}
		for result in results:
			forms[result[0]] = result

		c.close()
		print forms
		return render(request, "quality/search.html", {"results":forms, 'agents': agents, 'languages': languages, 'supervisors': supervisors, 'messages': messages, 'fields':fields, 'dropdowns':dropdowns})

	return render(request, "quality/search.html", {'agents': agents, 'languages': languages, 'supervisors': supervisors, 'messages': messages, 'fields':fields, 'dropdowns':dropdowns})


@login_required()
def formActionv2(request, form_n='Phone', form = -1):

	#Setup variables to keep track of variables for options in page
	agents = []
	languages = {}
	fields = {}
	overview = {}
	errors = {}
	messages = []
	evaluator = request.user
	supervisor = {}
	form_name = form_n + "-Form"

	#Run queries to retrieve the list of agents & language

	sup_id = request.user.profile.id
	sup_name = request.user.first_name + " " + request.user.last_name
	supervisor = {sup_id: sup_name,}

	agents_obj = User.objects.filter(groups__name='Agent').order_by('first_name')

	for agent in agents_obj:
		temp = {}
		temp['name'] = agent.first_name + " " + agent.last_name
		temp['id'] = agent.profile.id
		agents.append(temp)

	languages_obj = Language.objects.all()

	for language in languages_obj:
		languages[language.id] = language.name

	q_form = Form.objects.filter(valid = True).filter(name = form_name)[0]

	q_sections = Section.objects.filter(form = q_form).order_by('order')

	form_render = []

	for q_section in q_sections:
		section = {}
		section['name'] = q_section.name
		section['weight'] = q_section.weight
		section['id'] = q_section.id

		questions = []
		q_questions = Question.objects.filter(section = q_section).order_by('order')

		for q_question in q_questions:
			question = {}
			question['question'] = q_question.question
			question['weight'] = q_question.weight
			question['id'] = q_question.id

			q_answers = Response.objects.filter(question = q_question.id).order_by('weight')

			answers = []
			for q_answer in q_answers:
				answer = {}
				answer['name'] = q_answer.answer
				answer['weight'] = q_answer.weight
				answers.append(answer)
			question['answers'] = answers

			questions.append(question)
		section['questions'] = questions
		form_render.append(section)

	query = "SELECT name FROM ops_system.service s where s.name like 'Payportal::%' order by name"

	c = connection.cursor()

	c.execute(query)

	results = c.fetchall()
	service = []
	for result in results:
		service.append(result[0])

	c.close()

	is_agent = False

	group = request.user.groups.values_list('name', flat=True)

	if "Agent" in group:
		is_agent = True

	#Action the form when submitted, and evaluate the form.
	if request.POST:

		for key, value in request.POST.items():
			pattern = re.compile("^([\w]+)([\d]+)$")

			if pattern.match(key):
				fields[key] = value
			elif "select" in key or "input" in key or "calendar" in key:
				overview[key] = value

		#print(fields)

		if request.POST['form_id'] != "-1" and form == -1:
			form = int(request.POST['form_id'])

		if 'selectAgentName' not in request.POST:
			errors['agentName'] = "Agent Name is required"

		if 'selectLanguage' not in request.POST:
			errors['language'] = "Language is required"

		if len(request.POST['inputWalletNumber']) == 0:
			errors['walletNumber'] = "Wallet NUmber is required"

		if len(request.POST['calendarDateCall']) == 0:
			errors['dateCall'] = "Date of Call is required"

		if len(request.POST['inputProgramName']) == 0:
			errors['inputProgramName'] = "Program Name is required"

		if len(request.POST['inputRecordingFile']) == 0:
			errors['recordingFile'] = "Recording File is required"

		if 'selectEvalType' not in request.POST:
			errors['evalType'] = "Evaluation Type is required"

		if len(request.POST['calendarDateEval']) == 0:
			errors['dateEval'] = "Date of Evaluation is required"

		if 'selectPrimaryReason' not in request.POST:
			errors['selectPrimaryReason'] = "Primary Reason for contact is required"


		if errors:
			return render(request, 'quality/form_v2.html', {'errors': errors, 'supervisor': supervisor, 'agents': agents, 'languages': languages, 'form':form_render, 'service':service, "fields": fields, "overview": overview, 'form_id': form ,'is_agent':is_agent, 'form_type': form_n})
		else:
			#Evaluate if the form was submited vs udated
			if form == -1:
				try:
					pattern = re.compile("^([\d]+)$")

					status = 0

					if str(request.POST['selectStatus']) == "1":
						status = 1

					f = Form_Overview(created_by = request.user.profile, score = overview['inputTotalScore'], status = status)
					f.save()

					form = f.id

					for k, v in fields.items():
						#fix to look up the key for comments based on section instead of id
						key = str(k).replace("select", "").replace("comments", "").replace("input", "")
						if key == "status":
							continue
						q = None
						if "input" in k:
							q = Question.objects.filter(section_id = key).filter(weight = 0.00)[0]
						else:
							q = Question.objects.get(id = key)
						answer_q = Evaluation(field=str(k), value=str(v), question=q, form_overview = f)
						answer_q.save()

					for k, v in overview.items():
						key = str(k).replace("select", "")
						answer_q = Form_Evaluation(field=str(k), value=str(v), form_overview = f)
						answer_q.save()
					messages.append("New record created successfully. The evaluation ID is: " + str(f.id))
				except Exception as e:
					#send error back that there was an issue
					print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
					errors['unableSave'] = "There was an error saving the form, please try again"
					#errors['error'] = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno) + " " + type(e).__name__ + e
			elif(int(form) > -1):

				form_ov = Form_Overview.objects.get(pk = form)

				status = 0
				if str(request.POST['selectStatus']) == "1":
					status = 1

				form_ov.status = status
				form_ov.save()
				try:
					for k, v in fields.items():
						key = str(k).replace("select", "").replace("comments", "").replace("input", "")
						if key == "status":
							continue
						q = None
						if "input" in key:
							q = Question.objects.filter(section_id = key).filter(weight = 0.00)[0]
						else:
							q = Question.objects.get(id = key)

						try:
							answer_q = Evaluation.objects.get(field=str(k), form_overview = form)
							answer_q.value = v
							answer_q.question = q
							answer_q.save()
						except:
							if "input" in k:
								q = Question.objects.filter(section_id = key).filter(weight = 0.00)[0]
							else:
								q = Question.objects.get(id = key)

							answer_q = Evaluation(field=str(k), value=str(v), question=q, form_overview = form_ov)
							answer_q.save()

					for k, v in overview.items():
						key = str(k).replace("select", "")
						try:
							answer_q = Form_Evaluation.objects.get(field=str(k), form_overview = form)
							answer_q.value = v
							answer_q.save()
						except:
							key = str(k).replace("select", "")
							answer_q = Form_Evaluation(field=str(k), value=str(v), form_overview = form_ov)
							answer_q.save()

					messages.append("Evaluation ID " + str(form) + " has been updated.")
				except Exception as e:
					#send error back that there was an issue
					print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
					errors['unableSave'] = "There was an error saving the form, please try again"
					#errors['error'] = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno) + " " + type(e).__name__ + e
	elif int(form) > -1:

		overview_q = Form_Evaluation.objects.filter(form_overview = form)

		for o_q in overview_q:
			overview[o_q.field] = o_q.value

		#print(overview)

		field_q = Evaluation.objects.filter(form_overview = form)

		for f_q in field_q:
			fields[f_q.field] = f_q.value

		sup = Profile.objects.get(pk = overview['selectEvalName'])

		supervisor[overview['selectEvalName']] = sup.user.first_name + " " + sup.user.last_name

		if is_agent and str(overview['selectAgentName']) != str(request.user.profile.id):
			errors['notauth'] = "You are not authorize to see this evaluation"
			fields = {}
			overview = {}

		#print(overview)
		#print(fields)

	c.close()
	#print(fields)
	return render(request, 'quality/form_v2.html', {'errors': errors, 'agents': agents, 'languages': languages, 'supervisor': supervisor, 'messages': messages, 'fields':fields, 'overview':overview, 'form':form_render, 'service':service, 'form_id':form, 'is_agent':is_agent, 'form_type': form_n})

@login_required()
def formSearchv2(request):
	#Setup variables to keep track of variables for options in page
	agents = []
	languages = {}
	fields = {}
	dropdowns = {}
	errors = {}
	messages = []
	supervisors = []
	sections = []

	is_agent = False

	group = request.user.groups.values_list('name', flat=True)

	if "Agent" in group:
		is_agent = True

	sups_obj = User.objects.filter(Q(groups__name='Supervisor') | Q(groups__name="Director") | Q(groups__name="TeamLead") | Q(groups__name="QA") | Q(groups__name="Training")).order_by('first_name')
	#print(sups_obj.query)
	for agent in sups_obj:
		temp = {}
		temp['name'] = agent.first_name + " " + agent.last_name
		temp['id'] = agent.profile.id
		supervisors.append(temp)

	agents_obj = User.objects.filter(groups__name='Agent').order_by('first_name')

	if is_agent:
		agents_obj = User.objects.filter(pk = request.user.id)

	for agent in agents_obj:
		temp = {}
		temp['name'] = agent.first_name + " " + agent.last_name
		temp['id'] = agent.profile.id
		agents.append(temp)

	languages_obj = Language.objects.all()

	for language in languages_obj:
		languages[language.id] = language.name

	if request.POST:
		#print(request.POST)
		tz = pytz.timezone(request.user.profile.location.iso_name)
		form_search = Form_Evaluation.objects.all()
		searchq = Q()
		for key, value in request.POST.items():
			if "select" in key or "input" in key or "calendar" in key:
				if len(value) > 0:
					fields[key] = value
					if "calendarDateEval" in key and "submit" not in key:
						if key == "calendarDateEvalFrom":
							date_search = datetime.strptime(fields['calendarDateEvalFrom'], "%Y-%m-%d")
							searchq = searchq & (Q(form_overview__created_time__gte = tz.localize(date_search)))
						else:
							date_search = datetime.strptime(fields['calendarDateEvalTo'], "%Y-%m-%d")
							searchq = searchq & (Q(form_overview__created_time__lte = tz.localize(date_search)))
						continue
					searchq = searchq | (Q(field = key) & Q(value = value))

		if is_agent and 'selectAgentName' not in fields:
			print("adding agent")
			fields['selectAgentName'] = str(agents[0]['id'])
			searchq = searchq | (Q(field = 'selectAgentName') & Q(value = agents[0]['id']))

		form_search = form_search.filter(searchq).order_by('-form_overview_id')

		#print(form_search.query)
		#print(agents[0]['id'])
		#print(len(form_search))
		#print(fields)
		forms = {}
		forms_list = []
		if form_search:
			for f_s in form_search:
				if is_agent and f_s.form_overview.status == 0:
					continue
				if f_s.form_overview.id not in forms:
					ev = Evaluation.objects.filter(form_overview = f_s.form_overview)[0]
					qu = Question.objects.get(pk = ev.question.id)
 					se = Section.objects.get(pk = qu.section.id)
					fo = Form.objects.get(pk = se.form.id)
					t = fo.name
					t = t.replace("-Form", "")
					forms[f_s.form_overview.id] = None
					form_dict = {}
					form_dict[f_s.form_overview.id] = {t:{}}
					f_search = Form_Evaluation.objects.filter(form_overview = f_s.form_overview)
					for f in f_search:
						if f.field in fields:
							if fields[f.field] != f.value:
								del forms[f_s.form_overview.id]
								break
						if "Agent" in f.field or "EvalName" in f.field:
							try:
								a = Profile.objects.get(pk = f.value)
								form_dict[f.form_overview.id][t][f.field] = a.user.first_name + " " + a.user.last_name
							except:
								continue
						elif "Language" in f.field:
							l = Language.objects.get(pk = f.value)
							form_dict[f.form_overview.id][t][f.field] = l.name
						else:
							form_dict[f.form_overview.id][t][f.field] = f.value

						status = "Draft"
						if f.form_overview.status == 1:
							status = "Final"
						form_dict[f.form_overview.id][t]["status"] = status
					if f_s.form_overview.id in forms:
						forms_list.append(form_dict)

		#print(forms_list)

		return render(request, "quality/search_v2.html", {"results":forms_list, 'agents': agents, 'languages': languages, 'supervisors': supervisors, 'messages': messages, 'fields':fields, 'dropdowns':dropdowns})


	return render(request, "quality/search_v2.html", {'agents': agents, 'languages': languages, 'supervisors': supervisors, 'messages': messages, 'fields':fields, 'dropdowns':dropdowns})

@login_required()
def requestData(request):

	errors = {}

	if request.POST:

		if len(request.POST['calendarDateEvalFrom']) == 0:
			errors['dateEvalFrom'] = "Date of From Evaluation is required"

		if len(request.POST['calendarDateEvalTo']) == 0:
			errors['dateEvalTo'] = "Date of To Evaluation is required"

		if errors:
			return render(request, "quality/get_data.html", {"errors": errors,})

		start_time = datetime.strptime(request.POST['calendarDateEvalFrom'], "%Y-%m-%d")
		end_time = datetime.strptime(request.POST['calendarDateEvalTo'], "%Y-%m-%d")
		#today = pytz.utc.localize(today)

		timezone = request.user.profile.location.iso_name

		tz = pytz.timezone(timezone)

		start_t = start_time
		end_t = end_time

		start_format = start_t.strftime("%Y-%m-%d %H:%M:%S")
		end_format = end_t.strftime("%Y-%m-%d %H:%M:%S")

		query = "SELECT qfo.id, au.first_name, au.last_name, CONVERT_TZ(qfo.created_time, 'UTC', '{}'), qfo.score, qq.question, qe.value, qq.weight FROM quality_form_overview qfo INNER JOIN utils_profile up on qfo.created_by_id = up.id INNER JOIN auth_user au on up.user_id = au.id INNER JOIN quality_evaluation qe on qe.form_overview_id = qfo.id INNER JOIN quality_question qq on qq.id = qe.question_id WHERE qfo.created_time between '{}' and '{}' ORDER BY qfo.id, qq.section_id, qq.`order`".format(timezone, start_format, end_format)

		with connection.cursor() as cur:
			cur.execute(query)
			overviews = cur.fetchall()

		start_format = start_t.strftime("%Y%m%d%H%M%S")
		end_format = end_t.strftime("%Y%m%d%H%M%S")

		f_name = "quality{}.csv".format(start_format+end_format,)

		file_name = os.path.join(os.path.realpath(""), "eve_site")
		file_name = os.path.join(file_name, "tmp")
		file_name = os.path.join(file_name, f_name)

		print(file_name)

		with open(file_name, 'wb') as f:
			writer = csv.writer(f)
			writer.writerow(["form_id", "agent_first_name", "agent_last_name", "evaluation_date", "score", "question", "value", "weight"])
			writer.writerows(overviews)

		filename = file_name # Select your file here.
		wrapper = FileWrapper(file(filename))
		response = HttpResponse(wrapper, content_type='text/plain')
		response['Content-Length'] = os.path.getsize(filename)
		response['Content-Disposition'] = 'attachment; filename={}'.format(f_name,)
		return response

	return render(request, "quality/get_data.html", {"errors": errors,})
