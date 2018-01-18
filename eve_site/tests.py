# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 07:47:20 2018

@author: emota
"""

from django.urls import resolve
from django.test import TestCase
from views import home_page

class HomePageTest(TestCase):
	
	def test_root_url_resolves_to_home_page_view(self):
		found = resolve('/')
		self.assertEqual(found.func, home_page)
		
		
	def test_home_page_returns_correct_html(self):
		response = self.client.get('/')
		html = response.content.decode('utf8')
		self.assertIn('<html>', html)
		self.assertIn('<title>Dashboard | CS Ops</title>', html)
		self.assertIn('<a href="/" class="brand-logo center">CS Ops 360 </a>', html)
		self.assertIn('<a href="" data-activates="slide-out" class="button-collapse show-on-large right"><i class="material-icons">menu</i></a>', html)
		self.assertIn('<i class="material-icons">menu</i>', html)
		self.assertTrue(html.endswith('</html>'))
		
	def test_home_page_uses_dashboard_template(self):
		response = self.client.get('/')
		self.assertTemplateUsed(response, 'site/dashboard.html')
		self.assertTemplateUsed(response, 'site/base.html')