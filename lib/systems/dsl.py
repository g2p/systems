# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.registry import Registry


def resource_type(typename):
  return Registry.get_singleton().resource_types.lookup(typename)

def transition_type(typename):
  return Registry.get_singleton().transition_types.lookup(typename)

def resource(typename, **valdict):
  t = resource_type(typename)
  i = t.make_instance(valdict)
  return i

def resource_ref(typename, **id_valdict):
  t = transition_type(typename)
  i = t.make_ref(id_valdict)
  return i

def transition(typename, **instructions_valdict):
  t = transition_type(typename)
  i = t.make_instance(instructions_valdict)
  return i

def ensure_resource(context, typename, **valdict):
  r = resource(typename, valdict)
  r = context.ensure_resource(r)
  return r

