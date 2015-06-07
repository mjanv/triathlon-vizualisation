from flask import Flask, render_template
from flask import request, redirect
from flask import make_response

import modele
import pandas as pd

import base64

app = Flask(__name__,static_url_path='/static')

@app.route('/')
def render_index():
    return render_template('index.html', title="",L=[],form=[])

@app.route('/chooseyear', methods = ['POST'])
def chooseyear():
    year = request.form['year']
    T = modele.TRICLAIRModele()
    L = T.get_list_triathlons(int(year))
    form = zip(list(L['name'] + L['format']),list(L['link']))
    return render_template('index.html', title="List of triathlons " + year,L=L.values.tolist(),form=form)

@app.route('/choosetriathlon', methods = ['POST'])
def choosetriathlon():
    T = modele.TRICLAIRModele()
    print request.form
    if request.form['max']:
        L = T.get_data_triathlon(link=request.form['tri']).head(int(request.form['max']))
    return render_template('index.html',title="",L=L.values.tolist(),form=[])

@app.route('/chooseathlete', methods = ['POST'])
def choosetathlete():
    return render_template('index.html',title="",L=[],form=[])         

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