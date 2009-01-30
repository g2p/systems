# vim: set fileencoding=utf-8 sw=2 ts=2 et :

class RegistryDict(object):
  """
  A registry for named items.

  Items must have a 'name' property.
  """

  def __init__(self):
    self.__dict = {}

  def register(self, item):
    if item.name in self.__dict:
      raise RuntimeError(u'Already registered: «%s»' % self.__dict[item.name])
    self.__dict[item.name] = item

  def lookup(self, name):
    return self.__dict[name]

  def __iter__(self):
    return iter(self.__dict)

class Registry(object):
  """
  A registry for various types and things.
  """

  def __new__(cls):
    if hasattr(cls, '_singleton'):
      raise RuntimeError('Singleton has already been instanciated')
    return super(type(cls), cls).__new__(cls)

  @classmethod
  def get_singleton(cls):
    """
    Get the singleton instance.
    """

    if not hasattr(cls, '_singleton'):
      setattr(cls, '_singleton', cls())
    return getattr(cls, '_singleton')

  def __init__(self):
    self.__transition_types = RegistryDict()
    self.__collectors = RegistryDict()

  @property
  def transition_types(self):
    return self.__transition_types

  @property
  def collectors(self):
    return self.__collectors

