#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import pandas as pd
import inspect
import os

def echo(msg=''):
	def echo_inside(fn):
	    def wrapped(*v, **k):
	        if v[0].verbose:
	        	print ":: Calling %s: %s" % (fn.__name__,msg)
	        	if v[1:] is not ():
	        		print " - Arguments: %s" % " , ".join(map(str,v[1:]))
	        		print v,k
	        		print inspect.getargspec(fn)[0]
	        return fn(*v, **k) 
	    return wrapped
	return echo_inside

def save_hdf(name,*args):
	def save_inside(fn):
		def wrapped(*v,**k):
			file_name = "".join((v[0].store_data,name,)+tuple([str(v[inspect.getargspec(fn)[0].index(arg)]) for arg in args]))
			if os.path.isfile(file_name):
				return pd.read_hdf(file_name,'df')
			else:	
				res = fn(*v,**k)
				res.to_hdf(file_name,key='df',mode='w')
				return res
		return wrapped
	return save_inside