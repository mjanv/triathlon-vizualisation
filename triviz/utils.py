#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import pandas as pd
from datetime import datetime,timedelta
import unicodedata, string

import matplotlib.pyplot as plt
import numpy as np
import scipy
import math

from scipy.stats import norm
import matplotlib.mlab as mlab

from pandas.tools.plotting import scatter_matrix

from itertools import combinations
from scipy.stats.stats import pearsonr
import matplotlib.cm as cm

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
	""" Normalize a column of timedelta to the percentage (>100%) of the first element """
	J = map(lambda x: float(x.total_seconds()) if isinstance(x,timedelta) else float('nan'),list(df))
	return map(lambda x: 100.0*x/J[0],J)

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


def plot_data_triathlon(triathlon_info,rankings,head=None,name=None,filters=None,returnfig=False):
	""" Plot interesting data about triathlon """

	nb_athletes = len(rankings)
	if head is not None:
		rankings = rankings.head(head)
	rankings = pd.concat([rankings.loc[:,:'Sexe'],rankings.loc[:,'Scratch':].apply(normalize_col)],axis=1).dropna()

	if name is not None:
		resultat=rankings[rankings['Nom']==name]

	if filters is not None:
		pass # TODO	

	figs = []	

	# Plot Correlation beetween Variable
	fig, axes = plt.subplots(ncols=3, nrows=2); axes = axes.ravel()
	fig.tight_layout(pad=2.0, w_pad=2.0, h_pad=2.0)
	#fig.suptitle(" ".join((triathlon_info['name'],str(triathlon_info['date'].year))),fontsize=12)
	cl  = cm.get_cmap('gist_rainbow',6)

	for ind, titles in enumerate(combinations(['Scratch','Natation','Velo','Cap'],2)):
		datas = [rankings[title] for title in titles]
		limit_low = int(min(map(min,datas))); limit_high = int(max(map(max,datas)))
		axes[ind].plot(datas[0],datas[1],'o',color=cl(ind),markersize=10)
		axes[ind].plot(xrange(limit_low,limit_high),xrange(limit_low,limit_high),'--k',linewidth=1)
		cor = np.corrcoef(zip(*[(a,b) for a,b in zip(datas[0],datas[1]) if not (math.isnan(a) or math.isnan(b))]))[0][1]

		if name is not None:
			axes[ind].plot(resultat[titles[0]],resultat[titles[1]],'D',color='black',markersize=10) 

		axes[ind].set_title('Correlation: ' + str(cor),fontsize=10)
		axes[ind].set_xlim([limit_low,limit_high]); axes[ind].set_ylim([limit_low,limit_high])
		axes[ind].set_xlabel(titles[0] + ' (% winner)'); axes[ind].set_ylabel(titles[1] +' (% winner)')
	figs.append(fig)

	# Plot Histogram distributions
	fig, axes = plt.subplots(ncols=2, nrows=2); axes = axes.ravel()
	for ind, title in enumerate(['Scratch','Natation','Velo','Cap']):
		data = rankings[title]
		(mu,sigma) = norm.fit(data)
		n, bins, patches = axes[ind].hist(data, nb_athletes/10, facecolor=cl(ind), alpha=0.4)
		if name is not None:
			axes[ind].axvline(resultat[title].values[0],color='red',linestyle='dashed')
		axes[ind].plot(bins, max(bins)*mlab.normpdf(bins, mu, sigma), '-',color='gray', linewidth=4,label=r'$\mu=%.3f,\ \sigma=%.3f$' %(mu, sigma))
		axes[ind].legend(loc='best', fancybox=True, framealpha=0.5)
		axes[ind].set_ylabel('Number of athletes')
		axes[ind].set_xlabel(title + ' (% winner)')
	fig.tight_layout()
	figs.append(fig)	

	# Plot Scratch Rankings	
	fig = plt.figure()
	ax = fig.add_subplot(111)
	plt.plot(rankings['Scratch'],'y')
	if name is not None:
		plt.plot(resultat['Place'],resultat['Scratch'],'D',color='black',markersize=15) 
	ax.set_xlabel('Classement'); ax.set_ylabel('Temps scratch (% vainqueur)')
	figs.append(fig)	
	print figs
	if returnfig:
		return figs
	else:	
		plt.show()	


					
if __name__ == '__main__':
	from utils import *
	from modele import *
	T = TRICLAIRModele()
	A=T.get_list_triathlons(2014)
	tri=A.loc[2]
	B=T.get_data_triathlon(tri.link,2014)
	plot_data_triathlon(tri,B)	