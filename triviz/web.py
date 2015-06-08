from flask import Flask, render_template
from flask import request, redirect
from flask import make_response

import urllib

import modele
import utils
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import StringIO

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

    print 'ERT'
    #import pdb; pdb.set_trace();
    images = utils.plot_data_triathlon(0,rankings=L,returnfig=True)
    print 'ZER'

    if request.form['max']:
        L = L.head(int(request.form['max']))

    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist()    



    return render_template('index.html',title=name,images=images)

@app.route('/chooseathlete', methods = ['POST'])
def choosetathlete():
    name,iden = request.form['athlete'].split(';')
    T = modele.TRICLAIRModele()
    L = T.get_data_athlete(iden) 
    table = dict()
    table['head'] = L.keys().tolist()
    table['rows'] = L.values.tolist() 
    fig = create_img(plotrandom())
  
    return render_template('index.html',title=name,table=table,images=[fig,fig])      

def plotrandom():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot([1,2,0,3,2,4,0])
    return fig   

def create_img(fig):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import StringIO
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    return 'data:image/png;base64,{}'.format(urllib.quote(png_output.getvalue().encode('base64').rstrip('\n')))
         

if __name__ == "__main__":
    app.run()