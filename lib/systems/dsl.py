# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.registry import get_registry

def resource_type(typename):
  return get_registry().resource_types.lookup(typename)

def transition_type(typename):
  return get_registry().transition_types.lookup(typename)

def resource(typename, **valdict):
  t = resource_type(typename)
  i = t.make_instance(valdict)
  return i

def transition(typename, **instructions_valdict):
  t = transition_type(typename)
  i = t.make_instance(instructions_valdict)
  return i

