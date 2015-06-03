"""
Small snippets of code for manipulation of data
"""

def write_list_triathlon_to_html():
	""" Load the list of triathlons for all years and render it into a HTML table """
	import modele
	M = modele.TRICLAIRModele()
	list_triathlons = M.get_list_all_triathlons()
	f=open('list_triathlons.html','w')
	f.write("""<style> table { color: #333; font-family: Helvetica, Arial, sans-serif; width: 100%; border-collapse: collapse; border-spacing: 0; }\n
				td, th { border: 1px solid #CCC; height: 25px; }\n
				th { background: #F3F3F3; font-weight: bold; text-align: center;  }\n
				td { background: #FAFAFA; text-align: center; } </style>""")
	f.write(A.to_html().encode('utf8'))
	f.close()

# Test draw data triathlon
from utils import *
from modele import *
T = TRICLAIRModele()
A=T.get_list_triathlons(2014)
tri=A.loc[2]
B=T.get_data_triathlon(tri.link,2014)
plot_data_triathlon(B,tri)