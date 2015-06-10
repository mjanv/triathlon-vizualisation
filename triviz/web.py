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
triviz = modele.TRICLAIRModele()

@app.route('/')
def render_index():
    return render_template('index.html')

@app.route('/chooseyear', methods = ['POST'])
def chooseyear():
    year = int(request.form['year'])

    L = triviz.get_list_triathlons(year)
    R = triviz.get_ranking_athletes(year)

    form_select_triathlon = zip(map(lambda x: '  '.join(x),zip(L['name'].tolist(),L['format'].tolist())),L['link'].tolist())
    form_select_athlete   = dict(zip(R['name'].tolist(),R['id'].tolist()))

    return render_template('index.html',title="Liste des triathlons " + str(year),
                                        year=year,
                                        table=prepare_table(L),
                                        form_select_triathlon=form_select_triathlon,
                                        form_select_athlete = form_select_athlete)

@app.route('/choosetriathlon', methods = ['POST'])
def choosetriathlon():
    datas = []
    name_triathlon,link = request.form['tri'].split(';')
    
    L = triviz.get_data_triathlon(link)

    rank_max = int(request.form['max'] if request.form['max'] else len(L))
    name = request.form['athlete'] if request.form['athlete'] else None   
    images = utils.plot_data_triathlon(L,head=rank_max,name_athlete=name,returnfig=True)

    datas = datas + [('image',im) for im in images]
    datas = datas.append(('table',prepare_table(L.head(rank_max))))

    return render_template('data.html',title=name_triathlon,datas=datas)

@app.route('/chooseathlete', methods = ['POST'])
def chooseathlete():
    datas = []
    name_athlete,identifier,year = request.form['athlete'].split(';') 

    D = triviz.get_data_athlete(identifier) 
    L = triviz.get_list_triathlons(year) 

    links = sum([list(L['link'][(L['name']==course) & (L['format']==form)]) for course,form in zip(D['course'],D['format'])],[])
    triathlons  = [triviz.get_data_triathlon(link) for link in links] 

    resultats = []
    for triathlon,name,forma in zip(triathlons,D['course'],D['format']):
        tri = pd.concat([triathlon.loc[:,:'Sexe'],triathlon.loc[:,'Scratch':].apply(utils.normalize_col)],axis=1).dropna()
        resultat = tri[ (tri['Nom']== name_athlete) | 
                        (tri['Nom'] == ' '.join(name_athlete.split(' ',1)[::-1])) ]
        if resultat.empty: 
            resultat = pd.DataFrame(columns=resultat.columns,index=[0])
        resultats.append(resultat.loc[:,['Place','Scratch','Natation','Velo','Cap']].values[0].tolist())        
    resultats = pd.concat([D['course'],pd.DataFrame(resultats,columns=['Place','Scratch','Natation','Velo','Cap'])],axis=1)

    images = utils.plot_data_athlete(resultats.set_index('course'))
    df = resultats
    df['Place'] = df['Place'].apply(lambda x: str(int(x)) if not numpy.isnan(x) else 'Non connu')
    for c in ['Scratch','Natation','Velo','Cap']:
        df[c] = df[c].apply(lambda x: ('%03d%%' % int(x)) if not numpy.isnan(x) else 'Non connu')

    datas = datas + [('image',im[:100]) for im in images]
    datas = datas + [('table',prepare_table(df))]
    import pdb; pdb.set_trace()   
    print datas    
 
    return render_template('data.html',title=name_athlete,datas=D)     

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

        if '.htm' in obj:
            link = 'http://www.triclair.com' + obj    
            return '<a href="%s">%s</a>' % (link,link)
                
        return obj 
    except:
        return obj    

def prepare_table(P):
    return dict({ 'head': P.keys().tolist(), 'rows': P.values.tolist() })


if __name__ == "__main__":
    app.run(debug=True)