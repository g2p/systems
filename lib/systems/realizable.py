# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.typesystem import InstanceBase

__all__ = (
    'Realizable', 'EmptyRealizable', 'Transition',
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


class Transition(InstanceBase, Realizable):
  """
  A transition, representing an action on some part of the system.
  """

  def ensure_extra_deps(self, context):
    """
    Ensure any computed dependencies are present in context.

    Useful for dependencies that are automatically present,
    possibly set by parameters.
    """

    pass



