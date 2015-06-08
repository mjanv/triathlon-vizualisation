from flask import Flask, render_template
from flask import request, redirect
from flask import make_response
from flask import session

import modele
import utils

import time
import pandas

app = Flask(__name__,static_url_path='/static')

@app.route('/')
def render_index():
    return render_template('index.html')

@app.route('/chooseyear', methods = ['POST'])
def chooseyear():
    year = int(request.form['year'])
    #session['year'] = year
    T = modele.TRICLAIRModele()
    L = T.get_list_triathlons(year)
    L2 = T.get_ranking_athletes(year)
    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist()
    A = map(lambda x: '  '.join(x),zip(L['name'].tolist(),L['format'].tolist()))
    form = zip(A,L['link'].tolist())
    form2 = zip(list(L2['name']),list(L2['id']))
    return render_template('index.html',year=year, title="List of triathlons " + str(year),table=table,form=form,form2 = form2)

@app.route('/choosetriathlon', methods = ['POST'])
def choosetriathlon():
    name,link = request.form['tri'].split(';')
    T = modele.TRICLAIRModele()
    L = T.get_data_triathlon(link=link)

    images = utils.plot_data_triathlon(0,rankings=L,returnfig=True)

    if request.form['max']:
        L = L.head(int(request.form['max']))

    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist()    

    return render_template('index.html',title=name,table=table,images=images)

@app.route('/chooseathlete', methods = ['POST'])
def choosetathlete():
    import pdb; pdb.set_trace();
    name,iden,year = request.form['athlete'].split(';')
    T = modele.TRICLAIRModele()
    P = T.get_data_athlete(iden) 
    L = T.get_list_triathlons(int(year))
    links=sum([list(L['link'][(L['name']==course) & (L['format']==form)]) for course,form in zip(P['course'],P['format'])],[])
    tris = [T.get_data_triathlon(l,int(year)) for l in links]
    images = utils.plot_data_athlete(P,tris,name)


    table = dict()
    table['head'] = P.keys().tolist()
    table['rows'] = P.values.tolist() 
  
    return render_template('index.html',title=name,table=table,images=images)      

@app.template_filter('format_table')
def format_table(obj):
    if isinstance(obj,pandas.tslib.Timestamp):  
        return time.strftime('%d %B %Y',time.strptime(str(obj), "%Y-%m-%d %H:%M:%S"))

    if isinstance(obj,pandas.tslib.Timedelta):
        return '%02d:%02d:%02d' % (obj.hours,obj.minutes,obj.seconds)
            
    return obj        

if __name__ == "__main__":
    app.run()