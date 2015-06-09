#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import numpy as np
import scipy as sp
import pandas as pd

import matplotlib.pyplot as plt

import urllib
import bs4 as bs
import datetime
import re
import os.path

from deco import echo
from utils import *

from collections import OrderedDict


BASE_URL = u'http://www.triclair.com'
SEASON_URL = u'/resultats/challenge-triathlon-rhone-alpes.php?saison='
ATHLETE_URL = u'/resultats/challenge-rhone-alpes-detail-triathlete-'
START_YEAR = 2010

class TRICLAIRModele(object):
    _list_triathlons = {}
    _ranking_athletes = {}
    _data_triathlon = {}
    _data_athletes = {}

    def __init__(self,verbose=True,store_data='data/'):
        self.verbose = verbose
        self.store_data = store_data

    @echo('Loading list of triathlons')
    def get_list_triathlons(self,year):
        year = int(year)
        if year not in self._list_triathlons:
            self._list_triathlons[year] = self.__load_list_triathlons(year)
        return self._list_triathlons[year]

    @echo('Loading list of triathlons for each year')
    def get_list_all_triathlons(self):
        return pd.concat([self.get_list_triathlons(year) for year in range(START_YEAR,datetime.datetime.today().year)])

    @echo('Loading ranking of athletes')
    def get_ranking_athletes(self,year):
        year = int(year)
        if year not in self._ranking_athletes:
            self._ranking_athletes[year] = self.__load_ranking_athletes(year)
        return self._ranking_athletes[year]

    @echo('Loading ranking of athletes for each year') 
    def get_all_ranking_athletes(self,year):
        return [(year,self.get_ranking_athletes(year)) for year in range(START_YEAR,datetime.datetime.today().year)]    

    @echo('Loading data of athlete')
    def get_data_athlete(self,iden):
        if iden not in self._data_athletes:
            self._data_athletes[iden] = self.__load_data_athlete(iden)
        return self._data_athletes[iden]    

    @echo('Loading data of triathlon')
    def get_data_triathlon(self,link):
        if link not in self._data_triathlon:
            self._data_triathlon[link] = self.__load_data_triathlon(link)
        return self._data_triathlon[link]               

    def __load_list_triathlons(self,year):
        """ Extract the table in the pages http://www.triclair.com/resultats/challenge-triathlon-rhone-alpes.php?saison=[year]
            which resumes the date, name, format, and link of each triathlon of the specified year. Returns a Pandas DataFrame. """ 
        file_name = self.store_data + 'list-triathlons-' + str(year) + '.csv'

        if os.path.exists(file_name):
            print('LALALALA')
            return pd.read_csv(file_name,encoding='utf8',
                            parse_dates=['date'], 
                            date_parser=pd.to_datetime).drop('Unnamed: 0',axis=1)

        if year not in range(START_YEAR,datetime.datetime.today().year):
            return None

        soup = self.__get_soup_webpage(BASE_URL + SEASON_URL + str(year))
        l = [(
              convertDate([a for a in line.previous_siblings][1].text), # date
              line.text, # name
              line.next_sibling[1:], # format
              line.get('href')[2:] # link
             ) 
            for line in soup.find_all('a',href=True) if '-resultats-' in line.get('href')]

        data = pd.DataFrame(l,columns=['date','name','format','link'])
        if self.store_data:
            data.to_csv(file_name, encoding='utf8')
        return data

    def __load_ranking_athletes(self,year):
        """ Extract the main table in the pages http://www.triclair.com/resultats/challenge-triathlon-rhone-alpes.php?saison=[year]
            which resumes the rank, name, sex, club and number of points of each athlete. Returns a Pandas. """  
        if year not in range(START_YEAR,datetime.datetime.today().year):
            return None

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

    def __load_data_athlete(self,iden):
        """ Extract the main table of an athlete's page knowing its id provided in the DataFrame computed by GetDataAthletes()
            which resumes the date, name, format (S,M,..), number of points, coefficient and total of each race. Returns a Pandas DataFrame. """    
        table = self.__get_soup_webpage(BASE_URL + ATHLETE_URL + str(iden) +'.htm').findAll('table')[1]
        sections  = ['date'     ,'course'        ,'format'   ,'points','coeff','total'] # Name sections for cleaning and converting data
        functions = [convertDate,lambda x: x[:-1],lambda x: x,int     ,int    ,int    ] # its attached function for cleaning and converting data
        columns = dict() 
        for row in table.find_all('tr')[3:-1]: # For all the rows except the headers and the last line (total of points)
            for sec,col,func in zip(sections,row.find_all('td'),functions): # For each columns of the rows
                columns.setdefault(sec,[]).append(func(col.text)) # clean and append the data
        return pd.DataFrame(columns)

    def __load_data_triathlon(self,link):
        """ TODO """
        file_name = self.store_data + link.split('.')[0] + '.csv'

        if os.path.exists(file_name):
            return pd.read_csv(file_name,encoding='utf8',
                            parse_dates=['Cap','Natation','Scratch','Velo'], 
                            date_parser=pd.to_timedelta).drop('Unnamed: 0',axis=1)



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
                    data =  'NON LICENCIE' if data == '' else data.upper()
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

        data = pd.DataFrame(columns)
        if self.store_data:
            data.to_csv(file_name, encoding='utf8')
        return data  

    def __get_soup_webpage(self,link):
        try:
            return bs.BeautifulSoup(urllib.urlopen(link).read())
        except IOError:
            return None 

