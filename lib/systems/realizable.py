# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.typesystem import InstanceBase

__all__ = (
    'Realizable', 'TypedRealizable', 'EmptyRealizable',
    'Resource', 'Transition',
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

class EmptyRealizable(Realizable):
  def realize(self):
    pass

class TypedRealizable(InstanceBase, Realizable):
  pass


class Resource(TypedRealizable):
  """
  A resource, representing a state of some part of the system.

  A resource has an identity that is common to all possible states.
  """

  pass


class TransitionBase(TypedRealizable):
  pass

class IdempotentTransition(TransitionBase):
  pass

class Transition(TransitionBase):
  """
  A transition, representing an action on some part of the system.
  """

  pass


