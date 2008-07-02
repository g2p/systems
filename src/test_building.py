from resource import ensure_resource, ref_resource
from context import global_context

import resources
resources.register()

ensure_resource('AptitudePackage',
    name='aptitude')
ensure_resource('AptitudePackage',
    name='grep',
    depends=[ref_resource('AptitudePackage', name='aptitude')])

def test_bundle(pkgname):
  """
  Bundles, to supersede puppet defines and classes.

  This is the manual way of doing it: a python function.
  """

  ensure_resource('AptitudePackage', name=pkgname)

test_bundle('doxygen')

gc = global_context()
gc.realize()

