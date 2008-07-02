from resource import add_resource
from resourcegraph import global_graph

import resources
resources.register()

add_resource('AptitudePackage', name='aptitude')

def test_bundle(pkgname):
  """
  Bundles, to supersede puppet defines and classes.

  This is the manual way of doing it: a python function.
  """

  add_resource('AptitudePackage', name=pkgname)

test_bundle('doxygen')

rg = global_graph()
rg.realize()

