# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.context import global_context
from systems.realizable import RealizableBase
from systems.registry import Registry

class TransitionBase(RealizableBase):
  pass

class IdempotentTransition(TransitionBase):
  pass

class Transition(TransitionBase):
  """
  A transition, representing an action on some part of the system.
  """

  pass


def ensure_transition(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().transition_types.lookup(typename)
  return t.ensure(valdict=kwargs, context=context, extra_deps=depends)

def ref_transition(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().transition_types.lookup(typename)
  return t.ensure_ref(valdict=kwargs, context=context, extra_deps=depends)

