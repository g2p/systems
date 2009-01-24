# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement

# use posixpath for platform-indepent paths
import os

from systems.registry import Registry
from systems.resource import Resource, ResourceType

__all__ = ('register', )

class FirstSentinel(Resource):
  """
  The first realized resource.
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('FirstSentinel', cls, ())
    Registry.get_singleton().resource_types.register(cls.__restype)

  def realize(self):
    pass

def register():
  FirstSentinel.register()

