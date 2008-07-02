from resource import call_resource
from resourcegraph import global_graph

import resources
resources.register()

call_resource('AptitudePackage', name='aptitude')

rg = global_graph()
rg.realize()

