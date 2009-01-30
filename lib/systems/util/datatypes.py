# vim: set fileencoding=utf-8 sw=2 ts=2 et :

__all__ = ('ImmutableDict', )

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

