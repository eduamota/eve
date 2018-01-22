# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 20:59:50 2018

@author: emota
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import unittest

class NewVisitorTest(unittest.TestCase):
	def setUp(self):
		self.browser = webdriver.Firefox()
		
	def tearDown(self):
		self.browser.quit()	
		
		
	def test_can_get_to_the_home_page(self):
		self.browser.get('http://localhost:8000')
		self.assertIn('Dashboard', self.browser.title)
		header_text = self.browser.find_element_by_class_name('brand-logo').text
		self.assertIn('CS Ops 360', header_text)
		
	def test_can_click_on_new_quelaity_form_link(self):
		self.browser.get('http://localhost:8000')
		newform = self.browser.find_element_by_link_text('Create a new form')
		newform.send_keys(Keys.ENTER)
		time.sleep(2)
		self.assertIn('Login', self.browser.title)
		
	def test_workforce_my_schedule_link(self):
		self.browser.get('http://localhost:8000')
		mySchedule = self.browser.find_element_by_link_text("My Schedule")
		mySchedule.send_keys(Keys.ENTER)
		time.sleep(1)
		
		fields = self.browser.find_elements_by_id("id_username")
		if len(fields) > 0:
			username = self.browser.find_element_by_id("id_username")
			pwd = self.browser.find_element_by_id("id_password")
			sub = self.browser.find_element_by_class_name("btn-primary")
			
			username.send_keys("emota")
			pwd.send_keys("L!$e)&abby12")
			sub.send_keys(Keys.ENTER)

		time.sleep(1)
		
		self.assertIn("My Schedule", self.browser.title)
		
	def test_workforce_team_schedule_link(self):
		self.browser.get('http://localhost:8000')
		mySchedule = self.browser.find_element_by_link_text("Team Schedule")
		mySchedule.send_keys(Keys.ENTER)
		time.sleep(1)
		
		fields = self.browser.find_elements_by_id("id_username")
		if len(fields) > 0:
			username = self.browser.find_element_by_id("id_username")
			pwd = self.browser.find_element_by_id("id_password")
			sub = self.browser.find_element_by_class_name("btn-primary")
			
			username.send_keys("emota")
			pwd.send_keys("L!$e)&abby12")
			sub.send_keys(Keys.ENTER)

		time.sleep(1)
		
		self.assertIn("Team Schedule", self.browser.title)
		
if __name__ == '__main__':
	unittest.main()
