# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 15:56:37 2017

@author: emota
"""

#!/usr/bin/python

import pickle
import cPickle
import numpy

from sklearn import cross_validation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectPercentile, f_classif



def preprocess(words_file = "your_word_data.pkl", authors_file="your_satisfaction.pkl"):
    """ 
        this function takes a pre-made list of email texts (by default word_data.pkl)
        and the corresponding authors (by default email_authors.pkl) and performs
        a number of preprocessing steps:
            -- splits into training/testing sets (10% testing)
            -- vectorizes into tfidf matrix
            -- selects/keeps most helpful features

        after this, the feaures and labels are put into numpy arrays, which play nice with sklearn functions

        4 objects are returned:
            -- training/testing features
            -- training/testing labels

    """

    ### the words (features) and authors (labels), already largely preprocessed
    ### this preprocessing will be repeated in the text learning mini-project
    with open(authors_file, "rb") as authors_file_handler:
        authors = cPickle.load(authors_file_handler)

    with open(words_file, "rb") as words_file_handler:
        word_data = cPickle.load(words_file_handler)
    

    ### test_size is the percentage of events assigned to the test set
    ### (remainder go into training)
    features_train, features_test, labels_train, labels_test = cross_validation.train_test_split(word_data, authors, test_size=0.1, random_state=42)



    ### text vectorization--go from strings to lists of numbers
    #vectorizer = TfidfVectorizer(sublinear_tf=True, min_df=0.2)
    vectorizer = TfidfVectorizer(sublinear_tf=True)
    features_train_transformed = vectorizer.fit_transform(features_train)
    features_test_transformed  = vectorizer.transform(features_test)
    #features



    ### feature selection, because text is super high dimensional and 
    ### can be really computationally chewy as a result
    #this can be switched to 40 and its a 79.61% acc
    selector = SelectPercentile(f_classif, percentile=10)
    selector.fit(features_train_transformed, labels_train)
    features_train_transformed = selector.transform(features_train_transformed)
    features_test_transformed  = selector.transform(features_test_transformed)
				
    labels = vectorizer.get_feature_names()

    ### info on the data
    #print "no. of Chris training emails:", sum(labels_train)
    #print "no. of Sara training emails:", len(labels_train)-sum(labels_train)
    
    return features_train_transformed, features_test_transformed, labels_train, labels_test, labels
    #return features_train, features_test, labels_train, labels_test