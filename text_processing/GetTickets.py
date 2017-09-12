# -*- coding: utf-8 -*-
"""
Created on Tue Aug 01 09:02:37 2017

@author: emota
"""

# -*- coding: utf-8 -*-
import sys
#from class_vis import prettyPicture
#from prep_terrain_data import makeTerrainData

from datetime import datetime, timedelta
from collections import defaultdict
import re
import math
import itertools
import collections
import unicodedata
from math import log, exp
from time import sleep
import time
from datetime import datetime, date
import MySQLdb

try:
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
except ImportError: # Python 2
    from urllib import urlencode
    from urllib2 import urlopen, Request
import json
import urllib2
import csv
import os
import pytz
import ssl
import base64
from threading import Thread, Event
import linecache

reload(sys)  
sys.setdefaultencoding('utf8')

exit = ''

class MethodRequest(Request):
  def __init__(self, *args, **kwargs):
	self._method = kwargs.pop('method', None)
	Request.__init__(self, *args, **kwargs)

  def get_method(self):
	return self._method if self._method else super(RequestWithMethod, self).get_method()

def getArticles(dayDiff):

	urlSession = 'https://otrs.hyperwallet.com/otrs/nph-genericinterface.pl/Webservice/RESTTicketConnector/SessionCreate'
	urlSearchTicket = 'https://otrs.hyperwallet.com/otrs/nph-genericinterface.pl/Webservice/RESTTicketConnector/TicketSearch'
	urlGetTicket = 'https://otrs.hyperwallet.com/otrs/nph-genericinterface.pl/Webservice/RESTTicketConnector/TicketGet'
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
			
	sessionID = ''
	
	try:
		conn = MySQLdb.connect(host="10.5.225.93",	# your host, usually localhost
		user='acepeda',		 # your username
		passwd='TeamIntel811',  # your password
		db="ops_system")		# name of the data base

		cur = conn.cursor()
		start_time = int(time.time())
		#print (start_time)
		#print (end_time-start_time)
		cur.execute('SELECT value_text from crd where system = "OTRS"')
		rows = cur.fetchall()
		sessionID = rows[0][0]
  
		pstTimeStart = datetime.now(pytz.timezone("UTC")).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=dayDiff)
		pstTimeStart = pstTimeStart.strftime('%Y-%m-%d %H:%M:%S')
  
		cur.execute('SELECT id from ticket where type_id = 9 and date(from_unixtime(unix_create_time)) = %s', (pstTimeStart, ))
		rows = cur.fetchall()
		for row in rows:
	
			payload = {"SessionID":sessionID, 
			"TicketID": row[0], 
			"AllArticles":1,
			"ArticleSenderType":["customer",], 
			"ArticleLimit":1, "Attachments":0} 
		
			req = MethodRequest(urlGetTicket, method='POST')
	
			r = urlopen(req, json.dumps(payload), context=ctx)
			data =  r.read()
			try: js = json.loads(str(data))
			except: js = None
			#print js
			if 'Error' in js:
				errorMessage = str(sys.exc_info())
				process = "Get Ticket Article"
				#print errorMessage
				#print process
				cur.execute('INSERT INTO log(Process, Error) Values (%s, %s)', (process, errorMessage,))
				conn.commit()
			else:
				try:
					js = js['Ticket'][0]['Article'][0]
					#print js
					cur.execute('REPLACE INTO article_content(id, content, subject, create_time) Values (%s, %s, %s, %s)', (js['ArticleID'], js['Body'].encode('utf8'), js['Subject'].encode('utf8'), js['CreateTimeUnix']))
					conn.commit()
				except:
					exc_type, exc_obj, tb = sys.exc_info()
					f = tb.tb_frame
					lineno = tb.tb_lineno
					filename = f.f_code.co_filename
					linecache.checkcache(filename)
					line = linecache.getline(filename, lineno, f.f_globals)
					#print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)
					continue
	except:
		exc_type, exc_obj, tb = sys.exc_info()
		f = tb.tb_frame
		lineno = tb.tb_lineno
		filename = f.f_code.co_filename
		linecache.checkcache(filename)
		line = linecache.getline(filename, lineno, f.f_globals)
		print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


i = 60
while i < 120:
	print i
	getArticles(i)
	i = i+1

