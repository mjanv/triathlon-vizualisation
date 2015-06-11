#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import urllib
import datetime
import StringIO
from itertools import combinations

import math
import numpy as np
from scipy.stats import norm

import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.cm as cm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


def convertDate(s):
    """ Convert a string under the format of day-month-year into a datetime object. None in case of failure """
    return datetime.datetime.strptime(s,'%d-%m-%Y')

def convertChrono(s):
    """ Convert a string under the format of hours:minutes:seconds into a timedelta object """
    s = map(int,s.strip().split(':'))
    return datetime.timedelta(hours=s[0],minutes=s[1],seconds=s[2])

def normalize_col(df):
    """ Normalize a column of timedelta to the percentage (>100%) of the first element """
    J = map(convert_timedelta,list(df))
    return map(lambda x: 100.0*x/J[0],J)

def create_img(fig):
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    return 'data:image/png;base64,{}'.format(urllib.quote(png_output.getvalue().encode('base64').rstrip('\n')))    

def convert_timedelta(td):
    if isinstance(td,np.timedelta64):
        return float(td.astype('timedelta64[s]')/np.timedelta64(1, 's'))
    elif isinstance(td,datetime.timedelta): 
        return float(td.total_seconds())
    else:
        return float('nan')          

def plot_data_triathlon(rankings,head=None,name_athlete=None,filters=None,returnfig=False):
    """ Plot interesting data about triathlon """

    nb_athletes = len(rankings)
    if head is not None:
        rankings = rankings.head(head)
    rankings = pd.concat([rankings.loc[:,:'Sexe'],rankings.loc[:,'Scratch':].apply(normalize_col)],axis=1).dropna()

    if name_athlete is not None:
        resultat=rankings[(rankings['Nom']== name_athlete) | (rankings['Nom'] == ' '.join(name_athlete.split(' ',1)[::-1]))]

    if filters is not None:
        pass # TODO 

    figs = []   
    plt.style.use('ggplot')

    # Plot Correlation beetween Variable
    fig, axes = plt.subplots(ncols=3, nrows=2,figsize=(12,8)); axes = axes.ravel()
    fig.tight_layout(pad=4.0, w_pad=4.0, h_pad=4.0)
    cl  = cm.get_cmap('gist_rainbow',6)

    for ind, titles in enumerate(combinations(['Scratch','Natation','Velo','Cap'],2)):
        datas = [rankings[title] for title in titles]
        limit_low = int(min(map(min,datas))); limit_high = int(max(map(max,datas)))
        axes[ind].plot(datas[0],datas[1],'+',color=cl(ind),markersize=5)
        axes[ind].plot(xrange(limit_low,limit_high),xrange(limit_low,limit_high),'--k',linewidth=1)
        cor = np.corrcoef(zip(*[(a,b) for a,b in zip(datas[0],datas[1]) if not (math.isnan(a) or math.isnan(b))]))[0][1]

        if name_athlete is not None:
            axes[ind].plot(resultat[titles[0]],resultat[titles[1]],'D',color='white',markersize=5) 

        axes[ind].set_title('Correlation: ' + str(cor),fontsize=10)
        axes[ind].set_xlim([limit_low,limit_high]); axes[ind].set_ylim([limit_low,limit_high])
        axes[ind].set_xlabel(titles[0] + ' (% vainqueur)'); axes[ind].set_ylabel(titles[1] +' (% vainqueur)')
    figs.append(create_img(fig))

    # Plot Histogram distributions
    fig, axes = plt.subplots(ncols=2, nrows=2,figsize=(10,10)); axes = axes.ravel()
    for ind, title in enumerate(['Scratch','Natation','Velo','Cap']):
        data = rankings[title]
        (mu,sigma) = norm.fit(data)
        #nbins = round((max(data)-min(data))/(2*(np.percentile(data,0.75)-np.percentile(data,0.25))*len(data)**(-1.0/3)))
        n, bins, patches = axes[ind].hist(data,nb_athletes/10, facecolor=cl(ind), alpha=0.7)
        if name_athlete is not None:
            axes[ind].axvline(resultat[title].values[0],color='red',linestyle='dashed')
        axes[ind].plot(bins, max(bins)*mlab.normpdf(bins, mu, sigma), '-',color='gray', linewidth=4,label=r'$\mu=%.3f,\ \sigma=%.3f$' %(mu, sigma))
        axes[ind].legend(loc='best', fancybox=True, framealpha=0.5)
        axes[ind].set_ylabel('Number of athletes')
        axes[ind].set_xlabel(title + ' (% vainqueur)')
    fig.tight_layout()
    figs.append(create_img(fig))
    
    # Plot Scratch Rankings 
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(111)
    plt.plot(rankings['Scratch'],'y')
    if name_athlete is not None:
        ax.axvline(int(resultat['Place']),color='red',linestyle='dashed') 
    ax.set_xlabel('Classement'); ax.set_ylabel('Temps scratch (% vainqueur)')
    figs.append(create_img(fig))
    
    if returnfig:
        return figs
    else:   
        plt.show()  

def plot_data_athlete(resultats):  
    plt.style.use('ggplot')
    figs = []

    ax = resultats.plot(ylim=(90,round(max(map(max,resultats.values)))),kind='bar',rot=90,secondary_y=['Place'],figsize=(12,12))
    plt.tight_layout(pad=2.0, w_pad=2.0, h_pad=2.0)
    ax.set_ylabel('Temps (% vainqueur)')
    ax.right_ax.set_ylabel('Classement')
    figs.append(create_img(ax.get_figure()))

    # --> Disabled because of the older version of pandas on PyAny which does not support 'box' option
        #ax = resultats.plot(kind='box',use_index=True,secondary_y=['Place'],figsize=(12,12))
        #plt.ylabel('Temps (% vainqueur)')
        #figs.append(create_img(ax.get_figure()))    

    return figs
           


                    