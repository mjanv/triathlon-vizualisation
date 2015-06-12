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

app = Flask(__name__,static_url_path='/static')
triviz = modele.TRICLAIRModele(online_version=False)

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

    #L = [triviz.get_list_triathlons(year) for year in range(2010,2015)]
    R = [triviz.get_ranking_athletes(year) for year in range(2010,2015)]

    names = reduce(lambda x,y: set(x).union(set(y)),[r['name'][r['points']>8000] for r in R])

    datas = []
    template = '<a href="/chooseathlete?id=%d&name=%s&year=%d">%s</a><br \> Position: %d (%d points)'
    tab = pd.DataFrame(columns=['name','2010','2011','2012','2013','2014'],index=[0])
    for ind,name in enumerate(names):
        R_name = [r[r['name']==name] for r in R]
        tab.loc[ind]= [name] + [template % (r['id'].values[0],name,year,r['club'].values[0],r['ranking'].values[0],r['points'].values[0]) if not r.empty else '' for year,r in zip(range(2010,2015),R_name)]
        
    datas = datas + [('table',prepare_table(tab))]    

    return render_template('data.html',title="Tous les triathletes au dessus de 8000 points",datas=datas)

@app.route('/choosetriathlon', methods = ['POST','GET'])
def choosetriathlon():
    if request.method == 'POST':
        name_triathlon,link = request.form['tri'].split(';')
        max_request = request.form['max']
        athlete = request.form['athlete']
    else:    
        name_triathlon = request.args.get('tri')
        link = request.args.get('link')
        max_request = request.args.get('max')
        athlete = request.args.get('athlete')        
    print name_triathlon,max_request,link,athlete
    L = triviz.get_data_triathlon(link)

    rank_max = int(max_request if max_request else len(L))
    name = athlete if athlete else None   
    images = utils.plot_data_triathlon(L,head=rank_max,name_athlete=name)

    datas = [('image',im) for im in images]
    datas = datas + [('table',prepare_table(L.head(rank_max)))]

    title = (name_triathlon + ' [' + athlete + ']') if athlete else name_triathlon

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
    try:
        if isinstance(obj,pd.tslib.Timestamp):  
            return datetime.datetime.strptime(str(obj), "%Y-%m-%d %H:%M:%S").strftime('%d %B %Y')

        if isinstance(obj,pd.tslib.Timedelta):
            return '%02d:%02d:%02d' % (obj.hours,obj.minutes,obj.seconds)

        if isinstance(obj,numpy.timedelta64):
            return obj.tolist()   

        if isinstance(obj,str):
            if obj.endswith('.htm'):    
                link = 'http://www.triclair.com' + obj    
                return '<a href="%s">%s</a>' % (link,link)
                
        return obj 
    except:
        return obj    

def prepare_table(P):
    return dict({ 'head': P.keys().tolist(), 'rows': P.values.tolist() })


if __name__ == "__main__":
    app.run(debug=True)