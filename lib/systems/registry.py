# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.util.datatypes import Named
from systems.typesystem import ResourceType, TransitionType
from systems.collector import Collector


__all__ = ( 'get_registry', )


class RegistryDict(object):
  """
  A registry for named items.

  Items must be Named.
  """

  def __init__(self, pytype):
    self.__dict = {}
    self.__pytype = pytype

  def register(self, item):
    if not isinstance(item, Named):
      raise TypeError
    if not isinstance(item, self.__pytype):
      raise TypeError
    if item.name in self.__dict:
      raise RuntimeError(u'Already registered: «%s»' % self.__dict[item.name])
    self.__dict[item.name] = item

  def lookup(self, name):
    return self.__dict[name]

  def __iter__(self):
    return self.__dict.itervalues()

class Registry(object):
  """
  A registry for various types and things.
  """

  def __new__(cls):
    if hasattr(cls, '_singleton'):
      raise RuntimeError('Singleton has already been instanciated')
    return super(Registry, cls).__new__(cls)

  @classmethod
  def global_instance(cls):
    """
    Get the "singleton" instance.
    """

    if not hasattr(cls, '_global_instance'):
      setattr(cls, '_global_instance', cls())
    return getattr(cls, '_global_instance')

  def __init__(self):
    self.__resource_types = RegistryDict(ResourceType)
    self.__transition_types = RegistryDict(TransitionType)
    self.__collectors = RegistryDict(Collector)

  @property
  def transition_types(self):
    return self.__transition_types

  @property
  def resource_types(self):
    return self.__resource_types

  @property
  def collectors(self):
    return self.__collectors


def get_registry():
  return Registry.global_instance()


