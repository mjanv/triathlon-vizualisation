#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import pandas as pd
from datetime import datetime,timedelta
import unicodedata, string

import matplotlib.pyplot as plt
import numpy as np
import scipy

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

def get_mask(self,format=None,name=None):
	all_true = [True]*len(self.list_triathlons['format'])
	format = all_true if format is None else self.list_triathlons['format']==format
	name   = all_true if name   is None else map(lambda x: name in x,self.list_triathlons['name'])

	return [x&y for (x,y) in zip(format,name)]

def plot_data_all_triathlons(self,mask):
	data = [self.get_data_scratch_triathlon(n,f) for n,f in zip(self.list_triathlons['name'][mask],self.list_triathlons['format'][mask])]
		
	data2 = [normalize_col(d['Scratch'].dropna()) for d in data]	
	plt.style.use(u'ggplot')
	fig, ax1 = plt.subplots()
	ax1.boxplot(data2,vert=False)
	ytickNames = plt.setp(ax1, yticklabels=list(self.list_triathlons['name']))
	plt.setp(ytickNames, rotation=0, fontsize=8)
	ax1.set_xlim([90,300])
	ax1.set_xlabel('Temps scratch (% vainqueur)')
	ax1.set_ylabel('Triathlon')
	plt.show()


def plot_data_triathlon(L,tri):
	fig, axes = plt.subplots(ncols=2, nrows=2)
	ax1, ax2, ax3, ax4 = axes.ravel()
	fig.tight_layout(pad=2.0, w_pad=2.0, h_pad=2.0)
	fig.suptitle(" ".join((tri['name'],str(tri['date'].year))),fontsize=12)

	LN = normalize_col(L['Natation']); LNm = float(np.median(LN))
	LV = normalize_col(L['Velo']); LVm = float(np.median(LV)) 
	LC = normalize_col(L['Cap']); LCm = float(np.median(LC)) 
	LS = normalize_col(L['Scratch']);  LSm = float(np.median(LS)) 

	ax1.plot(LN,LV,'r+')
	ax1.plot(xrange(70,270),xrange(70,270),'--k',linewidth=1)
	ax1.plot([LNm,LNm],[70,LVm],'-k',linewidth=0.5)
	ax1.plot([70,LNm],[LVm,LVm],'-k',linewidth=0.5)

	ax1.set_xlim([70,270]); ax1.set_ylim([70,270])
	ax1.set_xlabel('Natation (% vainqueur)'); ax1.set_ylabel('Vélo (% vainqueur)')

	ax2.plot(LC,LN,'g+')
	ax2.plot(xrange(70,270),xrange(70,270),'--k',linewidth=1)
	ax2.plot([LCm,LCm],[70,LNm],'-k',linewidth=0.5)
	ax2.plot([70,LCm],[LNm,LNm],'-k',linewidth=0.5)
	ax2.set_xlim([70,270]); ax2.set_ylim([70,270])
	ax2.set_xlabel('Cap (% vainqueur)'); ax2.set_ylabel('Natation (% vainqueur)')
			
	ax3.plot(LV,LC,'b+')
	ax3.plot(xrange(70,270),xrange(70,270),'--k',linewidth=1)
	ax3.plot([LVm,LVm],[70,LCm],'-k',linewidth=0.5)
	ax3.plot([70,LVm],[LCm,LCm],'-k',linewidth=0.5)
	ax3.set_xlim([70,270]); ax3.set_ylim([70,270])
	ax3.set_xlabel('Vélo (% vainqueur)'); ax3.set_ylabel('Cap (% vainqueur)')

	ax4.plot(LS,'y')
	ax4.set_xlim([70,270]); ax4.set_ylim([70,270])
	ax4.set_xlabel('Classement'); ax4.set_ylabel('Temps scratch(% vainqueur)')
	ax4.autoscale(tight=True)
					
	mng = plt.get_current_fig_manager()
	mng.full_screen_toggle()
	plt.show()	