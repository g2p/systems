# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.util.datatypes import Named


class Collector(Named):
  """
  Groups several transitions into one.

  It is the responsibility of the caller to pass transitions
  that are compatible dependency-wise
  (ie don't have dependencies paths linking them).
  """

  def __init__(self, name):
    Named.__init__(self, name)

  def partition(self, realizables):
    """
    Break up a sequence of collectible transitions into a partition.

    A partition is a sequence of sequences, the inner sequences
    being transitions that may be collected together.

    The default implementation is to have a partition made of
    a single part containing everything.
    """

    return (realizables, )

  def filter(self, realizable):
    """
    Return True for transitions we may collect, False otherwise.
    """

    raise NotImplementedError('filter')

  def collect(self, transitions):
    """
    Build one Aggregate from many Resource.
    """

    raise NotImplementedError('collect')


class Aggregate(object):
  """
  Apes Resource somewhat.

  get_extra_deps will not be called due to a sane stage system,
  override place_transitions.
  """

  def place_transitions(self, transition_graph):
    # Override this.
    raise NotImplementedError

  @property
  def identity(self):
    # identities do not make much sense here.
    return self


