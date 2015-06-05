from flask import Flask, render_template
from flask import request, redirect

import modele
import pandas as pd

app = Flask(__name__,static_url_path='/static')



@app.route('/')
def hello_world():
    return render_template('index.html', author="", title="Triathlon Viz",L=[])

@app.route('/signup', methods = ['POST'])
def signup():
    name = request.form['name']
    year = request.form['year']
    T = modele.TRICLAIRModele()
    L = T.get_list_triathlons(int(year))
    L = L[L['name'].str.contains(name)]
    L = map(lambda x: x,L.values.tolist())
    print L
    return render_template('index.html', author="", title="List of triathlons " + year,L=L)
    #return redirect('/')

if __name__ == "__main__":
    app.run()