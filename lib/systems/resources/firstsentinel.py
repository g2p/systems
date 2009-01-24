# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from systems.registry import Registry
from systems.resource import Resource
from systems.typesystem import Type

__all__ = ('register', )

class FirstSentinel(Resource):
  """
  The first realized resource.
  """

  @classmethod
  def register(cls):
    cls.__restype = Type('FirstSentinel', cls, ())
    Registry.get_singleton().resource_types.register(cls.__restype)

  def realize(self):
    pass

def register():
  FirstSentinel.register()

