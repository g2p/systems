# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.util.datatypes import Named
from systems.typesystem import ResourceBase, Expandable


class Collector(Named):
  """
  Groups several transitions into one.

  It is the responsibility of the caller to pass transitions
  that are compatible dependency-wise
  (ie don't have dependencies paths linking them).
  """

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
    Build one Aggregate from many CResource.
    """

    raise NotImplementedError('collect')


class CResource(ResourceBase):
  """
  A marker class. Those must not be expanded.
  """

  pass


class Aggregate(Expandable):
  """
  This is expanded once, and stands in for several CResource.
  """

  def expand_into(self, resource_graph):
    # Caveat: Only add transitions, not resources.
    raise NotImplementedError

