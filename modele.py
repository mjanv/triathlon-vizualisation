#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import numpy as np
import scipy as sp
import pandas as pd

import matplotlib.pyplot as plt
import Tkinter

import sys, urllib
import bs4 as bs
import re
from datetime import datetime,timedelta
import time
import logging
import getopt
import os.path
import unicodedata, string
import inspect

from collections import Counter, OrderedDict

BASE_URL = u'http://www.triclair.com'
SEASON_URL = u'/resultats/challenge-triathlon-rhone-alpes.php?saison='
ATHLETE_URL = u'/resultats/challenge-rhone-alpes-detail-triathlete-'

def echo(msg=''):
	def echo_inside(fn):
	    def wrapped(*v, **k):
	        if v[0].verbose:
	        	print ":: Calling %s: %s" % (fn.__name__,msg)
	        	if v[1:] is not ():
	        		print " - Arguments: %s" % " , ".join(map(str,v[1:]))
	        		print v,k
	        		import inspect
	        		print inspect.getargspec(fn)[0]
	        	#self.log.log(logging.INFO,"Calling %s: %s" % (fn.__name__,msg))
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

class TRICLAIRBase(object):
	_instance = None

	def __init__(self):
		pass

	def __printlog(self,msg,lvl=logging.INFO):
		if self.verbose:
			self.log.log(lvl,msg)

class TRICLAIRControler(object):
	def __init__(self,verbose=False,store_data='data/'):
		self.verbose = verbose
		self.store_data = store_data

		self.modele = TRICLAIRModele(verbose,store_data)
		self.view = TRICLAIRView(None,self)

		self.log = logging.getLogger()
		self.log.setLevel(logging.INFO)
		self.log.handlers = []
		stream_handler = logging.StreamHandler() 
		stream_handler.setLevel(logging.INFO)
		self.log.addHandler(stream_handler)	

	def launch(self):	
		self.view.mainloop()	 		

	def trigger(self,tr):
		res =  self.modele.get_list_triathlons(2014) 
		print res
		for ind,r in enumerate(res['name']+res['format']):
			self.view.Lb1.insert(ind,r)
		self.view.labelVariable.set("Done")
	


class TRICLAIRModele(object):
	_list_triathlons = {}
	_ranking_athletes = {}
	_data_triathlon = {}
	_data_athletes = {}

	def __init__(self,verbose=True,store_data='data/'):
		self.verbose = verbose
		self.store_data = store_data

	@echo('Loading list of triathlons')
	def get_list_triathlons(self,year=datetime.today().year-1):
	    if year not in self._list_triathlons:
	        self._list_triathlons[year] = self.__load_list_triathlons(year)
	    return self._list_triathlons[year]

	@echo('Loading ranking of athletes')    
	def get_ranking_athletes(self,year=datetime.today().year-1):
	    if year not in self._ranking_athletes:
	        self._ranking_athletes[key] = self.__load_ranking_athletes(year)
	    return self._ranking_athletes[key]

	@echo('Loading data of athlete')
	def get_data_athlete(self,identifier):
	    if identifier not in self.data_athletes:
	        self.data_athletes[identifier] = self.__load_data_athlete(year)
	    return self._data_athletes[identifier]	

	@echo('Loading data of triathlon')
	def get_data_triathlon(self,link,name='',format='',year=datetime.today().year-1):
		if link not in self._data_triathlon:
			self._data_triathlon[link] = self.__load_data_triathlon(link,name,format,year)
		return self._data_triathlon[link]	   	    	

	@save_hdf('list_triathlons','year')
	def __load_list_triathlons(self,year=datetime.today().year-1):
		""" Extract the table in the pages http://www.triclair.com/resultats/challenge-triathlon-rhone-alpes.php?saison=[year]
			which resumes the date, name, format, and link of each triathlon of the specified year. Returns a Pandas DataFrame. """	
		soup = self.__get_soup_webpage(BASE_URL + SEASON_URL + str(year))
		l = [(convertDate([a for a in line.previous_siblings][1].text), line.text,line.next_sibling[1:],line.get('href')[2:]) 
		    for line in soup.find_all('a',href=True) if '-resultats-' in line.get('href')]

		return pd.DataFrame(l,columns=['date','name','format','link'])

	@echo('Loading ranking of athletes from %s' % BASE_URL)
	@save_hdf('ranking_athletes','year')
	def __load_ranking_athletes(self,year=datetime.today().year-1):
		""" Extract the main table in the pages http://www.triclair.com/resultats/challenge-triathlon-rhone-alpes.php?saison=[year]
			which resumes the rank, name, sex, club and number of points of each athlete. Returns a Pandas. """
		table = self.__get_soup_webpage(BASE_URL + SEASON_URL + str(year)).findAll('table')[2]
		columns = dict()
		for ind,row in enumerate(table.find_all('tr')[2:]): # for all the rows without the header
			col = row.find_all('td') # For all the columns
			columns.setdefault('ranking',[]).append(int(col[0].text)) # 0: extract the rank
			columns.setdefault('id',     []).append(re.findall('[0-9]+',str(col[1]))[0]) # 1: extract the id of the athlete
			columns.setdefault('sex',    []).append(u'F' if [a for a in col[1].find_all('a', href=True,style=True)] else u'M') # 2: extract sex of athlete with presence of "style" tag (=pink=female='F')	
			columns.setdefault('name',   []).append(" ".join(col[1].text.split())) # 3: extract name, club and number of points
			columns.setdefault('club',   []).append(col[2].text[:-1])
			columns.setdefault('points', []).append(int(col[3].text))
		return pd.DataFrame(columns).replace(u'',u'NON LICENCIE')

	@save_hdf('athlete','id')	
	def load_data_athlete(self,id):
		""" Extract the main table of an athlete's page knowing its id provided in the DataFrame computed by GetDataAthletes()
			which resumes the date, name, format (S,M,..), number of points, coefficient and total of each race. Returns a Pandas DataFrame. """	
		table = bs.BeautifulSoup(urllib.urlopen(BASE_URL + ATHLETE_URL + str(identifier) +'.htm').read()).findAll('table')[1]
		sections  = ['date'     ,'course'        ,'format'   ,'points','coeff','total']	# Name sections for cleaning and converting data
		functions = [convertDate,lambda x: x[:-1],lambda x: x,int     ,int    ,int    ] # its attached function for cleaning and converting data
		columns = dict() 
		for row in table.find_all('tr')[3:-1]: # For all the rows except the headers and the last line (total of points)
			for sec,col,func in zip(sections,row.find_all('td'),functions): # For each columns of the rows
				columns.setdefault(sec,[]).append(func(col.text)) # clean and append the data
		return pd.DataFrame(columns)

	@save_hdf('triathlon','year','name','format')	
	def __load_data_triathlon(self,link,name='',format='',year=datetime.today().year-1):
 			
		table = self.__get_soup_webpage(BASE_URL + link).findAll('table')[-1]

		entete = map(lambda x: x.text,table.find_all('tr')[0].find_all('th'))
		useful = [u'Place',u'Nom',u'Club',u'Cat.',u'Sexe',u'Temps scratch',u'Nat.',u'V\xe9lo',u'C\xe0p']
		translation = dict({u'Place':u'Place',u'Nom':u'Nom',u'Club':u'Club',u'Cat.':u'Categorie',u'Sexe':u'Sexe',
							u'Temps scratch':u'Scratch',u'Nat.':u'Natation',u'V\xe9lo':u'Velo',u'C\xe0p':u'Cap'})
		sections     = list(set(entete).intersection(set(useful)))
		not_sections = list(set(useful).difference(set(entete)))

		columns = OrderedDict()
		re_search = re.compile('[0-1]?[0-9]:[0-9]+:[0-9]+')
		re_search2 = re.compile('[0-9]+:[0-9]+')
		for col in useful:
			columns.setdefault(translation[col],[])

		for row in table.find_all('tr')[1:]:
			col = row.find_all('td')
			for sec in sections:
				data = col[entete.index(sec)].text.strip()
				if sec == u'Nom':
					data = data.upper()
					if u'Pr\xe9nom' in entete:
						data = u' '. join((data,col[entete.index(u'Pr\xe9nom')].text.upper().strip()))
				elif sec ==u'Place':
					data = int(data)
				elif sec == u'Club':
					data = 	'NON LICENCIE' if data == '' else data.upper()
				elif sec == u'Sexe':
					data = u'M' if data in ['M','m','H','h'] else (u'F' if data in ['F','f','W','w'] else u'NaN')
				elif sec == u'Cat.':
					pass
				elif sec in [u'Temps scratch',u'Nat.',u'V\xe9lo',u'C\xe0p']:
					if col[entete.index(u'Temps scratch')].text.strip() in ['DNF','DSQ','DNS']:
						data = float('nan')
					else:	
						data = convertChrono(re_search.findall(data)[0]) if re_search.match(data) else (convertChrono('00:' + re_search2.findall(data)[0]) if re_search2.match(data) else float('nan'))                 			
				
				columns[translation[sec]].append(data)
			for sec in not_sections:
				data = float('nan')
				columns[translation[sec]].append(data)	

		return pd.DataFrame(columns)	

	def __get_soup_webpage(self,link,_cache={}):
	    if link not in _cache:
	        _cache[link] = bs.BeautifulSoup(urllib.urlopen(link).read())
	    return _cache[link]

class TRICLAIRView(Tkinter.Tk):
    def __init__(self,parent,controler):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.controler = controler
        self.initialize()

    def initialize(self):
    	self.title('TRICLAIR Data Visualization')
    	self.grid()

        self.entry = Tkinter.Entry(self)
        self.entry.grid(column=0,row=0,sticky='EW')

        button = Tkinter.Button(self,text=u"Download",command=self.OnButtonClick)
        button.grid(column=0,row=1)
        button2 = Tkinter.Button(self,text=u"Plot",command=self.plotdata_tri)
        button2.grid(column=1,row=1)

        self.Lb1 = Tkinter.Listbox(self,selectmode=Tkinter.BROWSE)
        self.Lb1.pack(fill=Tkinter.BOTH, expand=1)
        self.Lb1.grid(column=0,row=2,columnspan=2)

        self.labelVariable = Tkinter.StringVar()
        label = Tkinter.Label(self,textvariable=self.labelVariable,anchor="w",fg="white",bg="blue")
        label.grid(column=0,row=3,columnspan=2,sticky='EW')

    def OnButtonClick(self):
    	self.labelVariable.set("Get list of 2014!")
    	self.controler.trigger('getlist')
    	print  self.Lb1.curselection()
        print "You clicked the button !"   

    def plotdata_tri(self):
		list_triathlons = self.controler.modele.get_list_triathlons(2014)
		for l,n,f in zip(list_triathlons['link'],list_triathlons['name'],list_triathlons['format']):
			S = self.controler.modele.get_data_triathlon(l,n,f,2014)
			print S['Scratch'].dropna()

def convertDate(s):
	""" Convert a string under the format of day-month-year into a datetime object. None in case of failure """
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

if __name__ == '__main__':
	A=TRICLAIRControler()
	A.launch()

