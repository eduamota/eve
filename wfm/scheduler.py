# -*- coding: utf-8 -*-
"""
Created on Wed Nov 08 07:42:54 2017

@author: emota
"""
from __future__ import unicode_literals

from time import sleep
import MySQLdb

def runScheduler(self):
	conn = MySQLdb.connect(host="localhost",	# your host, usually localhost
						 user="emota",		 # your username
						 passwd="L!$e)&abby12",  # your password
						 db="ops_system")		# name of the data base

	cur = conn.cursor()
	
	keepRunning = True
	
	while keepRunning:
		#Queued - 1
		#Running - 2
		#Success - 3
		#Failed - 4
		
		cur.execute('Select * from wfm_job where status_id = 3 and job_type = "Scheduler"')
		jobs = cur.fetchall()
		
		if len(jobs) > 0:
			keepRunning == False
			break

		cur.execute('Select * from wfm_job where status_id = 1 and job_type != "Scheduler"')
		j = cur.fetchall()
		
		for jb in j:
			if jb[1] == "Insert_Shifts":
				cur.execute('Update wfm_job set status_id = 2 where id = %s', (jb[0],))
				sDate = jb[2]
				eDate = jb[3]
				cUser = jb[4]
				aUser = jb[6]
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
		print "Another loop"
		sleep(1)