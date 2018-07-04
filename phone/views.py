# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
try:
	from urllib.parse import urlencode
	from urllib.request import urlopen, Request
except ImportError: # Python 2
	from urllib import urlencode
	from urllib2 import urlopen, Request
from django.db import connection
import json
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.decorators import user_passes_test

# Create your views here.
class MethodRequest(Request):
  def __init__(self, *args, **kwargs):
	self._method = kwargs.pop('method', None)
	Request.__init__(self, *args, **kwargs)

  def get_method(self):
	return self._method if self._method else super(RequestWithMethod, self).get_method()


def callAPI(met, url, data = False):

	c = connection.cursor()

	c.execute("SELECT account_id, value_text from ops_system.crd where System = 'Voxter'")
	authToken = c.fetchone()
	account_id = authToken[0]
	authToken = authToken[1]

	url = url.replace("{accountID}", account_id)

	req = MethodRequest(url, method=met)
	req.add_header('Content-Type', 'application/json')
	req.add_header('X-Auth-Token', authToken)
	r = {}
	if met == "POST" and data:
		dataDic = {'data':data, "verb":"POST"}
		r = urlopen(req, json.dumps(dataDic))
	else:
		r = urlopen(req)
	c.close()
	return json.loads(str(r.read()))


@xframe_options_exempt
@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def agents(request, agentid = False):
	agents = callAPI("GET", 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/users');
	agentData = agents['data']
	agentList = {}
	agentQueues = {}
	queue = {}
	notQueue = {}
	messages = {}
	c = connection.cursor()
	if request.POST:
			#print request.POST
			status = ""
			results = {"status": "error"}
			if "agentState" in request.POST:
				status = request.POST["agentState"]
				url = "https://api-hw.voxter.com:8443/v1/accounts/{accountID}/agents/" + agentid + "/status"

				if "login" in request.POST["agentState"] or "logout" in request.POST["agentState"] or "resume" in request.POST["agentState"]:
					data = {"status":request.POST["agentState"]}
				else:
					data = {"status":"pause", "alias":request.POST["agentState"]}
				results = callAPI("POST", url, data)

			elif "agentQueueGroup" in request.POST and len(request.POST['reasonChange']) > 0:
				url = 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/agents/' + agentid + '/queue_status'
				requestText = "Logout Agent: " +agentid + " Queues:"
				qs = request.POST.getlist('agentQueueGroup')
				for q in qs:
					#print q
					data = {"action":"logout", "queue_id":q}
					results = callAPI("POST", url, data)
					requestText = requestText + " " + q
					c.execute("INSERT INTO queue_management_log (request, comments) VALUES ('" + requestText + "', '" + request.POST['reasonChange'] + "')")
				status = "Log out of selected queues"
			elif "queueName" in request.POST and len(request.POST['reasonChange2']) > 0:
				url = 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/agents/' + agentid + '/queue_status'
				requestText = "Login Agent: " +agentid + " Queues:"
				qs = request.POST.getlist('queueName')
				for q in qs:
					#print q
					data = {"action":"login", "queue_id":q}
					results = callAPI("POST", url, data)
					requestText = requestText + " " + q
					c.execute("INSERT INTO queue_management_log (request, comments) VALUES ('" + requestText + "', '" + request.POST['reasonChange2'] + "')")
				status = "Log in of selected queues"
			elif len(request.POST['reasonChange2']) == 0 or len(request.POST['reasonChange']) == 0:
				status = "change the queue, you need to provide a reason for the change"

			if results['status'] == "success":
				messages["Success " + status] = "green"
			else:
				messages["Error unable to " + status] = "red"

	for agent in agentData:
		agentList[agent['id']] = agent['first_name'] + " " + agent['last_name']

	if agentid and len(agentid) > 10:
		queueNames = callAPI("GET", 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/queues')

		for q in queueNames['data']:
			queue[q['id']] = q['name']

		queues = callAPI("GET", 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/agents/' + agentid)
		if "queues" in queues["data"]:
			for value in queues["data"]["queues"]:
				agentQueues[value] = queue[value]

		for k, v in queue.items():
			if k not in agentQueues:
				notQueue[k] = v


	c.close()
	return render(request, "phone/agents.html", {"agentList":agentList,"queues":agentQueues, "noQueues":notQueue, "agentid": agentid, "messages":messages})

@xframe_options_exempt
@user_passes_test(lambda u: u.groups.filter(name__in=['Admin', 'QA', 'TeamLead', 'Supervisor']).exists())
def queues(request, queueid = False):
	agents = callAPI("GET", 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/queues');
	queueData = agents['data']
	queueList = {}
	userList = {}
	user = {}
	notAgent = {}
	messages = {}
	c = connection.cursor()
	if request.POST:
			print request.POST
			status = ""
			results = {"status": "error"}
			if "agentQueueGroup" in request.POST and len(request.POST['reasonChange']) > 0:

				requestText = "Logout Queue: " +queueid + " Agents:"
				qs = request.POST.getlist('agentQueueGroup')
				for q in qs:
					url = 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/agents/' + q + '/queue_status'
					data = {"action":"logout", "queue_id":queueid}
					results = callAPI("POST", url, data)
					requestText = requestText + " " + q
					c.execute("INSERT INTO queue_management_log (request, comments) VALUES ('" + requestText + "', '" + request.POST['reasonChange'] + "')")
				status = "Log out of selected agents"
			elif "userName" in request.POST and len(request.POST['reasonChange2']) > 0:

				requestText = "Login Queue: " + queueid + " Agents:"
				qs = request.POST.getlist('userName')
				for q in qs:
					url = 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/agents/' + q + '/queue_status'
					data = {"action":"login", "queue_id": queueid}
					results = callAPI("POST", url, data)
					requestText = requestText + " " + q
					c.execute("INSERT INTO queue_management_log (request, comments) VALUES ('" + requestText + "', '" + request.POST['reasonChange2'] + "')")
				status = "Log in of selected agents"
			elif len(request.POST['reasonChange2']) == 0 or len(request.POST['reasonChange']) == 0:
				status = "change agent queue, you need to provide a reason for the change"

			if results['status'] == "success":
				messages["Success " + status] = "green"
			else:
				messages["Error unable to " + status] = "red"

	for queue in queueData:
		queueList[queue['id']] = queue['name']

	if queueid and len(queueid) > 10:
		userNames = callAPI("GET", 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/users')

		for agent in userNames['data']:
			user[agent['id']] = agent['first_name'] + " " + agent['last_name']

		queues = callAPI("GET", 'https://api-hw.voxter.com:8443/v1/accounts/{accountID}/queues/' + queueid)
		#print queues
		if "agents" in queues["data"]:
			for value in queues["data"]["agents"]:
				userList[value] = user[value]

		for k, v in user.items():
			if k not in userList:
				notAgent[k] = v


	c.close()
	return render(request, "phone/queues.html", {"agentList":queueList,"queues":userList, "noQueues":notAgent, "agentid": queueid, "messages":messages})

def issues(request):
	return render(request, "phone/issues.html")

def dashboard(request):
	return render(request, "phone/dashboard.html")
