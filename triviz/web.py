from flask import Flask, render_template
from flask import request, redirect
from flask import make_response

import modele
import pandas as pd

import base64

app = Flask(__name__,static_url_path='/static')

@app.route('/')
def render_index():
    print 'BITE1'
    return render_template('index.html')

@app.route('/chooseyear', methods = ['POST'])
def chooseyear():
    print 'BITE2'
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
    print 'BITE3'
    name,link = request.form['tri'].split(';')
    T = modele.TRICLAIRModele()
    L = T.get_data_triathlon(link=link)
    if request.form['max']:
        L = L .head(int(request.form['max']))
    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist()    

    return render_template('index.html',title=name,table=table)

@app.route('/chooseathlete', methods = ['POST'])
def choosetathlete():
    print 'BITE4'
    name,iden = request.form['athlete'].split(';')
    T = modele.TRICLAIRModele()
    L = T.get_data_athlete(iden) 
    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist() 

    return render_template('index.html',title=name,table=table)         

def create_img(fig):
    import StringIO
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
 
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    return png_output.getvalue()
    #response=make_response(png_output.getvalue())
    #response.headers['Content-Type'] = 'image/png'           

if __name__ == "__main__":
    app.run()