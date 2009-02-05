# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import


class ImmutableDict(object):
  """
  Proxy a dictionary into an immutable dictionary.

  This is as needed. We don't need the whole mapping protocol,
  and we don't rely on python 2.6 collections.Mapping.
  """

  def __init__(self, dct):
    self.__dct = dct

  def __getitem__(self, key):
    return self.__dct[key]

  def __contains__(self, key):
    return key in self.__dct

  def iteritems(self):
    return self.__dct.iteritems()

  def iterkeys(self):
    return self.__dct.iterkeys()

  def __iter__(self):
    return self.iterkeys()

  def keys(self):
    return self.__dct.keys()

  def _key(self):
    return frozenset(self.__dct.iteritems())

  def __hash__(self):
    return hash(self._key())

  def __cmp__(self, other):
    return -cmp(other, self._key())


class Named(object):
  def __init__(self, name):
    self.__name = name

  @property
  def name(self):
    return self.__name


