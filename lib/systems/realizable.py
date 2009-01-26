# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.typesystem import InstanceBase

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

