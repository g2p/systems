# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.registry import Registry
from systems.context import global_context
from systems.typesystem import InstanceRef
from systems.realizable import EmptyRealizable

__all__ = (
    'transition_type',
    'transition', 'ensure_transition', 'ref_transition',
    'ensure_anon',
    )

def transition_type(typename):
  return Registry.get_singleton().transition_types.lookup(typename)

def transition(typename, **kwargs):
  t = transition_type(typename)
  i = t.make_instance(valdict=kwargs)
  return i

def ensure_transition(typename, context=global_context(), depends=(), **kwargs):
  i = transition(typename, **kwargs)
  return context.ensure_realizable(i, extra_deps=depends)

def ref_transition(typename, context=global_context(), depends=(), **kwargs):
  t = transition_type(typename)
  i = InstanceRef(type=t, id_valdict=kwargs)
  return context.ensure_realizable(i, extra_deps=depends)

def ensure_anon(context=global_context(), depends=()):
  i = EmptyRealizable()
  return context.ensure_realizable(i, extra_deps=depends)

