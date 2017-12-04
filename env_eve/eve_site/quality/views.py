# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.contrib.auth.models import User
import re

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
