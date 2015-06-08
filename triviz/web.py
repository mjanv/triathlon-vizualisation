from flask import Flask, render_template
from flask import request, redirect
from flask import make_response

import modele
import utils


app = Flask(__name__,static_url_path='/static')

@app.route('/')
def render_index():
    return render_template('index.html')

@app.route('/chooseyear', methods = ['POST'])
def chooseyear():
    year = int(request.form['year'])
    T = modele.TRICLAIRModele()
    L = T.get_list_triathlons(year)
    L2 = T.get_ranking_athletes(year)
    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist()
    A = map(lambda x: '  '.join(x),zip(L['name'].tolist(),L['format'].tolist()))
    form = zip(A,L['link'].tolist())
    form2 = zip(list(L2['name']),list(L2['id']))
    return render_template('index.html', title="List of triathlons " + str(year),table=table,form=form,form2 = form2)

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
    name,iden = request.form['athlete'].split(';')
    T = modele.TRICLAIRModele()
    L = T.get_data_athlete(iden) 
    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist() 
  
    return render_template('index.html',title=name,table=table)      
         

if __name__ == "__main__":
    app.run()