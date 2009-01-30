# vim: set fileencoding=utf-8 sw=2 ts=2 et :

class Collector(object):
  """
  Groups several transitions into one.

  It is the responsibility of the caller to pass transitions
  that are compatible dependency-wise
  (ie don't have dependencies paths linking them).
  """

  def __init__(self, name):
    self.__name = name

  @property
  def name(self):
    return self.__name

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
    Build one realizable from multiple.
    """

    raise NotImplementedError('collect')

