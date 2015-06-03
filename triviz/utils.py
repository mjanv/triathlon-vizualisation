#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import pandas as pd
from datetime import datetime,timedelta
import unicodedata, string

def convertDate(s):
	""" Convert a string under the format of day-month-year into a datetime object. 
		None in case of failure 
	"""
	return datetime.strptime(s,'%d-%m-%Y')

def convertChrono(s):
	""" Convert a string under the format of hours:minutes:seconds into a timedelta object """
	strp = s.strip().split(':')
	return timedelta(hours=int(strp[0]),minutes=int(strp[1]),seconds=int(strp[2]))

def remove_accents(data):
	""" Remove accents and lower an unicode string """
	return ''.join(x for x in unicodedata.normalize('NFKD', data) if x in string.ascii_letters).lower()	

def triathlon_file_name(*args):
	return remove_accents("_".join(args).lower().replace(' \'','_'))

def normalize_col(df):
	J = map(lambda x: x.total_seconds() if isinstance(x,timedelta) else float('nan'),list(df))
	brn = float(J[0])
	J = map(lambda x: 100.0*float(x)/brn,J)
	return J	