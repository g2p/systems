# vim: set fileencoding=utf-8 sw=2 ts=2 et :


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

  def keys(self):
    return self.__dct.keys()


class Named(object):
  def __init__(self, name):
    self.__name = name

  @property
  def name(self):
    return self.__name


