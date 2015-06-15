from flask import Flask, render_template
from flask import request, redirect
from flask import make_response
from flask import session

import modele
import utils

import time
import numpy
import datetime
import pandas as pd

from collections import Counter

app = Flask(__name__,static_url_path='/static')
triviz = modele.TRICLAIRModele()

@app.route('/')
def render_index():
    return render_template('index.html')

@app.route('/chooseyear', methods = ['POST','GET'])
def chooseyear():
    year = int(request.form['year']) if request.method == 'POST' else request.args.get('year')

    L = triviz.get_list_triathlons(year)
    R = triviz.get_ranking_athletes(year)

    form_select_triathlon = zip(map(lambda x: '  '.join(x),zip(L['name'].tolist(),L['format'].tolist())),L['link'].tolist())
    form_select_athlete   = dict(zip(R['name'].tolist(),R['id'].tolist()))

    return render_template('index.html',title="Liste des triathlons " + str(year),
                                        year=year,
                                        table=prepare_table(L),
                                        form_select_triathlon=form_select_triathlon,
                                        form_select_athlete = form_select_athlete)

@app.route('/chooseallyears', methods = ['POST'])
def chooseallyears():

    L = [triviz.get_list_triathlons(year) for year in range(2010,2015)]
    R = [triviz.get_ranking_athletes(year) for year in range(2010,2015)]


    datas = []

    datas = datas + [('title',"Les 20 clubs les plus actifs entre 2010 et 2014")]
    C = Counter(sum([list(r['club']) for r in R],[])).most_common()[:20]
    tab = dict({'head':['club','nombre de triathletes'],'rows':C})
    datas = datas + [('table',tab)]

    datas = datas + [('title',"Tous les triathletes au dessus de 8000 points")]
    names = reduce(lambda x,y: set(x).union(set(y)),[r['name'][r['points']>8000] for r in R])
    template = '<a href="/chooseathlete?id=%d&name=%s&year=%d">%s</a><br \> Position: %d (%d points)'
    tab = pd.DataFrame(columns=['name','2010','2011','2012','2013','2014'],index=[0])
    for ind,name in enumerate(names):
        R_name = [r[r['name']==name] for r in R]
        tab.loc[ind]= [name] + [template % (r['id'].values[0],name,year,r['club'].values[0],r['ranking'].values[0],r['points'].values[0]) if not r.empty else '' for year,r in zip(range(2010,2015),R_name)]
    datas = datas + [('table',prepare_table(tab))]   

    datas = datas + [('title',"Les triathlons Rhone-Alpes entre 2010 et 2014")]
    for l in L:
        l = l.drop(['link'],axis=1)
        tab = prepare_table(l)
        datas = datas + [('table',tab)]

    return render_template('data.html',title="",datas=datas)

@app.route('/choosetriathlon', methods = ['POST','GET'])
def choosetriathlon():
    if request.method == 'POST':
        name_triathlon,link = request.form['tri'].split(';')
        max_request = request.form['max']
        athlete = request.form['athlete']
        femmes = 'femmes' in request.form
        hommes = 'femmes' in request.form
    else:    
        name_triathlon = request.args.get('tri')
        link = request.args.get('link')
        max_request = request.args.get('max')
        athlete = request.args.get('athlete')
        femmes = False
        hommes = False        
    
    L = triviz.get_data_triathlon(link)

    if femmes and hommes:
        pass
    else:    
        if femmes:  
            L = L[L['Sexe']=='F']  
        if hommes:  
            L = L[L['Sexe']=='M']   
   
    rank_max = int(max_request if max_request else len(L))
    name = athlete.upper() if athlete else None   
    images = utils.plot_data_triathlon(L,head=rank_max,name_athlete=name)

    datas = [('image',im) for im in images]
    datas = datas + [('table',prepare_table(L.head(rank_max)))]

    title = (name_triathlon + ' [' + athlete + ']') if athlete else name_triathlon

    print 'coucou'
    return render_template('data.html',title=title ,datas=datas)

@app.route('/chooseathlete', methods = ['POST','GET'])
def chooseathlete():
    if request.method == 'POST':
        name_athlete,identifier,year = request.form['athlete'].split(';') 
    else:
         name_athlete = request.args.get('name')
         identifier = request.args.get('id')
         year = request.args.get('year')   

    D = triviz.get_data_athlete(identifier) 
    L = triviz.get_list_triathlons(year) 

    links = sum([list(L['link'][(L['name']==course) & (L['format']==form)]) for course,form in zip(D['course'],D['format'])],[])
    triathlons  = [triviz.get_data_triathlon(link) for link in links] 

    resultats = []
    for triathlon,name,forma in zip(triathlons,D['course'],D['format']):
        tri = pd.concat([triathlon.loc[:,:'Sexe'],triathlon.loc[:,'Scratch':].apply(utils.normalize_col)],axis=1)
        resultat = tri[ (tri['Nom'] == name_athlete) | 
                        (tri['Nom'] == ' '.join(name_athlete.split(' ',1)[::-1])) |
                        (tri['Nom'] == name_athlete.replace ("-", " ")) | 
                        (tri['Nom'] == ' '.join(name_athlete.split(' ',1)[::-1]).replace ("-", " ")) 
                    ]
        if resultat.empty: 
            resultat = pd.DataFrame(columns=resultat.columns,index=[0])
        resultats.append(resultat.loc[:,['Place','Scratch','Natation','Velo','Cap']].values[0].tolist())     
    D['course'] = D['course'] + ' ' +  D['format'] 
    D['liens'] = ['<a href="http://www.triclair.com%s">Classement</a> - <a href="/choosetriathlon?&tri=%s&link=%s&athlete=%s">Analyse</a>' 
                    % (l,c,l,name_athlete) for c,l in zip(D['course'],links)]     
    resultats = pd.concat([D['course'],pd.DataFrame(resultats,columns=['Place','Scratch','Natation','Velo','Cap'])],axis=1)


    images = utils.plot_data_athlete(resultats.set_index('course'))
    df = pd.concat([resultats,D['liens']],axis=1)
    df['Place'] = df['Place'].apply(lambda x: str(int(x)) if not numpy.isnan(x) else 'Non connu')
    for c in ['Scratch','Natation','Velo','Cap']:
        df[c] = df[c].apply(lambda x: ('%03d%%' % int(x)) if not numpy.isnan(x) else 'Non connu')


    datas = [('image',im) for im in images]
    datas = datas + [('table',prepare_table(df))]  
 
    return render_template('data.html',title= ' - '.join((name_athlete,str(year))),datas=datas)     

@app.template_filter('format_table')
def format_table(obj):
    """ Jinja filter for formatting elements in <td></td> """
    if isinstance(obj,long):
        return str(datetime.timedelta(seconds=obj/10**9))

    if isinstance(obj,pd.tslib.Timestamp):  
        return datetime.datetime.strptime(str(obj), "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y')

    #Only available for pandas >0.15
    #if isinstance(obj,pd.tslib.Timedelta):
    #    return '%02d:%02d:%02d' % (obj.hours,obj.minutes,obj.seconds)

    if isinstance(obj,numpy.timedelta64):
        return obj.tolist()   

    if isinstance(obj,str):
        if obj.endswith('.htm'):    
            link = 'http://www.triclair.com' + obj    
            return '<a href="%s">%s</a>' % (link,link)

    return obj

def prepare_table(P):
    return dict({ 'head': P.keys().tolist(), 'rows': P.values.tolist() })


if __name__ == "__main__":
    app.run(debug=True)