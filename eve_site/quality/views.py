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
			return render(request, 'quality/default.html', {'errors': errors, 'supervisors': supervisors, 'agents': agents, 'languages': languages})
		else:
			#Evaluate if the form was submited vs udated
			if request.POST['action'] == "submit":
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
					messages.append("<script>Materialize.toast('New record created successfully. The evaluation ID is: " + str(formID) + "', 4000, 'green');</script>")
				except:
					#send error back that there was an issue
					messages.append("<script>Materialize.toast('Error unable to save form', 4000, 'red');</script>")
	elif int(form) > -1:
		c.execute("SELECT * FROM ops_system.quality_responses where form_id = %s", [form,])
		results = c.fetchall()
		
		for row in results:
			pattern = re.compile("^([\d]+)$")

			if pattern.match(row[2]) or row[2] == "evalType" or row[2] == "language" or row[2] == "agentName":
				dropdowns[row[2]] = row[3]
			else:
				fields[row[2]] = row[3]
		
	
	return render(request, 'quality/default.html', {'agents': agents, 'languages': languages, 'supervisor': supervisor, 'messages': messages, 'fields':fields, 'dropdowns':dropdowns})
