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

  def partition(self, resources):
    """
    Break up a sequence of collectible resources into a partition.

    A partition is a sequence of sequences, the inner sequences
    being resources that may be collected together.

    The default implementation is to have a partition made of
    a single part containing everything.
    """

    return (resources, )

  def filter(self, resource):
    """
    Return True for resources we may collect, False otherwise.
    """

    raise NotImplementedError('filter')

  def collect(self, context):
    """
    Build one realizable from multiple resources.
    """

    raise NotImplementedError('collect')

