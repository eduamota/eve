# -*- coding: utf-8 -*-
"""
Created on Mon May 07 17:54:50 2018

@author: emota
"""

from django.contrib.admin import AdminSite

class MyAdminSite(AdminSite):
	# Text to put at the end of each page's <title>.
	AdminSite.site_title = 'Admin'

	# Text to put in each page's <h1> (and above login form).
	AdminSite.site_header = 'CS Ops - Admin'

	# Text to put at the top of the admin index page.
	AdminSite.index_title = 'CS Ops'

admin_site = MyAdminSite()