#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import pandas as pd
from functools import wraps
import inspect
import os

def echo(msg=''):
	def echo_inside(fn):
	    def wrapped(*v, **k):
	        if v[0].verbose:
	        	print(":: Calling %s: %s" % (fn.__name__,msg))
	        return fn(*v, **k) 
	    return wrapped
	return echo_inside

def memo(fn):
    cache = {}
    @wraps(fn)
    def wrap(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]
    return wrap	

def save_hdf(name,*args):
	def save_inside(fn):
		def wrapped(*v,**k):
			file_name = "".join((v[0].store_data,name,)
								 +tuple([str(v[inspect.getargspec(fn)[0].index(arg)]) for arg in args]))
			if os.path.isfile(file_name):
				return pd.read_hdf(file_name,'df')
			else:	
				res = fn(*v,**k)
				res.to_hdf(file_name,key='df',mode='w')
				return res
		return wrapped
	return save_inside