# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 14:46:17 2017

@author: emota
"""

#!/usr/bin/python

import os
import pickle
import re
import sys
import MySQLdb
import pytz
#sys.path.append( "../tools/" )
from parse_out_text import parseOutText
from pre_processing import preprocess

from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from datetime import datetime, date
from datetime import datetime, timedelta
from collections import defaultdict
from class_vis import prettyPicture
from sklearn.cluster import KMeans

reload(sys)  
sys.setdefaultencoding('utf8')
#deine your username and password to connect to the ops_system datbaase
username = "emota"
password = "L!$e)&abby12"

#create a connection to the database using the password and username previously declared
conn = MySQLdb.connect(host="10.5.225.93",	# your host, usually localhost
user=username,		 # your username
passwd=password,  # your password
db="ops_system")		# name of the data base

cur = conn.cursor()
'''
pstTimeStart = datetime.now(pytz.timezone("UTC")).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=60)
pstTimeStart = pstTimeStart.strftime('%Y-%m-%d %H:%M:%S')

cur.execute("select s.name, concat(ac.subject, ' ' , ac.content) as content from article a, ticket t, article_content ac, dynamic_field_value d, service s where a.id = ac.id and a.ticket_id = t.id and t.service_id = s.id and d.object_id = t.id and d.value_text = 'English' and date(from_unixtime(a.unix_create_time)) >= %(sdate)s", {'sdate':pstTimeStart,})

results = cur.fetchall()

from_data = []
word_data = []

### temp_counter is a way to speed up the development--there are
### thousands of emails from Sara and Chris, so running over all of them
### can take a long time
### temp_counter helps you only look at the first 200 emails in the list so you
### can iterate your modifications quicker
temp_counter = 0

label_vector = []

for row in results:
    ### only look at first 200 emails when developing
    ### once everything is working, remove this line to run over full dataset
    email_parsed = ""
    if len(row[1]) > 0:
        #print row[2]
        email_parsed = parseOutText(unicode(row[1]))
        #print email_parsed
    ### use parseOutText to extract the text from the opened email

    ### use str.replace() to remove any instances of the words
    ### ["sara", "shackleton", "chris", "germani"]


    ### append the text to word_data
    if len(email_parsed) > 0:
        word_data.append(email_parsed)

    ### append a 0 to from_data if email is from Sara, and 1 if email is from Chris
        service_parts = row[0].split('::')
        index = 0	
        if service_parts[1] not in label_vector:
		label_vector.append(service_parts[1])
	  
        index = label_vector.index(service_parts[1])
								
        from_data.append(index)

cur.close()
conn.close()
print label_vector
print "comments processed"

#print word_data[152]
#print from_data[152]

pickle.dump( word_data, open("your_word_data.pkl", "wb") )
pickle.dump( from_data, open("your_satisfaction.pkl", "wb") )

cv =  CountVectorizer()
X = cv.fit_transform(word_data)
tfidf = TfidfTransformer()
feature_vector = tfidf.fit_transform(X)
feature_mapping = cv.get_feature_names()
#print cv.get_stop_words()

#print 'Mapped features size : ' + str(len(feature_mapping))
print feature_vector.shape
'''
features_train, features_test, labels_train, labels_test, labels  = preprocess()

from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

clf = SVC(kernel="rbf", gamma=1.8, C=1)
#clf = SVC(kernel="poly", degree=5, gamma=1.8, C=1.0)
#clf = SVC(decision_function_shape='ovo')

clf = clf.fit(features_train, labels_train)
pred = clf.predict(features_test)

#pred = clf.predict()


acc = accuracy_score(pred, labels_test)
print "accurracy: ", acc * 100




'''
km = KMeans(n_clusters=10, init='random', n_init=1, verbose=1)

km.fit(features_train)
print km.labels_
print km.labels_.shape
print km.cluster_centers_
print labels.shape
#plt = prettyPicture(clf, features_test, labels_test)
#plt.show()
'''




