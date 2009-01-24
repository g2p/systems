# vim: set fileencoding=utf-8 sw=2 ts=2 et :
import types

from systems.registry import Registry
from systems.transition import Transition
from systems.typesystem import Type, AttrType

__all__ = ('register', )

class PythonCode(Transition):
  """
  Arbitrary transition realized in code.
  """

  @classmethod
  def register(cls):
    cls.__type = Type('PythonCode', cls,
      [
      AttrType('name',
        identifying=True),
      AttrType('function',
        valid_condition=cls.is_valid_function),
      ])
    Registry.get_singleton().transition_types.register(cls.__type)

  @classmethod
  def is_valid_function(cls, function):
    return isinstance(function, types.FunctionType)

  def realize(self):
    f = self.attributes['function']
    f()

def register():
  PythonCode.register()

