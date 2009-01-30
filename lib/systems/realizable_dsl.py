# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.registry import Registry
from systems.context import global_context
from systems.typesystem import InstanceRef
from systems.realizable import EmptyRealizable

__all__ = (
    'ensure_resource', 'ref_resource',
    'ensure_transition', 'ref_transition',
    'ensure_anon',
    )

def ensure_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().resource_types.lookup(typename)
  i = t.make_instance(valdict=kwargs)
  return context.ensure_realizable(i, extra_deps=depends)

def ref_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().resource_types.lookup(typename)
  i = InstanceRef(type=t, id_valdict=kwargs)
  return context.ensure_realizable(i, extra_deps=depends)

def ensure_transition(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().transition_types.lookup(typename)
  i = t.make_instance(valdict=kwargs)
  return context.ensure_realizable(i, extra_deps=depends)

def ref_transition(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().transition_types.lookup(typename)
  i = InstanceRef(type=t, id_valdict=kwargs)
  return context.ensure_realizable(i, extra_deps=depends)

def ensure_anon(context=global_context(), depends=()):
  i = EmptyRealizable()
  return context.ensure_realizable(i, extra_deps=depends)

