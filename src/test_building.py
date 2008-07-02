from resource import call_resource
from resources.aptitudepackage import AptitudePackage
from resourcegraph import global_graph

call_resource('AptitudePackage', name='aptitude')

rg = global_graph()

rg.realize()

