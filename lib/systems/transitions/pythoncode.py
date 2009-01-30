# vim: set fileencoding=utf-8 sw=2 ts=2 et :
import types

from systems.registry import Registry
from systems.realizable import Transition
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
        pytype=types.FunctionType),
      # Positional arguments, a sequence
      AttrType('args',
        default_value=[],
        pytype=list),
      # Keyword arguments, a map
      AttrType('kargs',
        default_value={},
        pytype=dict),
      ])
    Registry.get_singleton().transition_types.register(cls.__type)

  def realize(self):
    f = self.attributes['function']
    a = self.attributes['args']
    k = self.attributes['kargs']
    f(*a, **k)

def register():
  PythonCode.register()

