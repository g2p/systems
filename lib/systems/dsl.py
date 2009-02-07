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

def resource_ref(typename, **valdict):
  t = resource_type(typename)
  i = t.make_ref(valdict)
  return i

def transition(typename, **instructions_valdict):
  t = transition_type(typename)
  i = t.make_instance(instructions_valdict)
  return i

def ensure_resource(context, typename, depends=(), **valdict):
  r = resource(typename, **valdict)
  r = context.ensure_resource(r)
  for dep in depends:
    context.ensure_dependency(dep, r)
  return r

def ensure_transition(context, typename, depends=(), **valdict):
  t = transition(typename, **valdict)
  t = context.ensure_transition(t)
  for dep in depends:
    context.ensure_dependency(dep, t)
  return t

