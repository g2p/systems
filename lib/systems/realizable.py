# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.context import global_context
from systems.registry import Registry
from systems.typesystem import InstanceBase

__all__ = ('Realizable', 'TypedRealizable',
    'Resource', 'ensure_resource', 'ref_resource',
    'Transition', 'ensure_transition', 'ref_transition',
    )


class Realizable(object):
  """
  Base for realizeable instances.

  Realising means applying to the current state of the system.
  A realizable can be put into a Context graph, where it has dependencies.
  Dependency relationships constrain the order of realization.
  Attributes determine realization.
  """

  def realize(self):
    """
    This will be called with all dependencies already realized.
    """

    raise NotImplementedError('realize')

class TypedRealizable(InstanceBase, Realizable):
  pass


class Resource(TypedRealizable):
  """
  A resource, representing a state of some part of the system.

  A resource has an identity that is common to all possible states.
  """

  pass


def ensure_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().resource_types.lookup(typename)
  return t.ensure(valdict=kwargs, context=context, extra_deps=depends)

def ref_resource(typename, context=global_context(), depends=(), **kwargs):
  t = Registry.get_singleton().resource_types.lookup(typename)
  return t.ensure_ref(valdict=kwargs, context=context, extra_deps=depends)


class TransitionBase(TypedRealizable):
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

