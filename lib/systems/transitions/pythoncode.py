# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import types

from systems.registry import Registry
from systems.typesystem import AttrType, TransitionType, Transition

__all__ = ('register', )

class PythonCode(Transition):
  """
  Arbitrary transition realized in code.
  """

  @classmethod
  def register(cls):
    cls.__type = TransitionType('PythonCode', cls,
        instr_type={
          'function': AttrType(
            pytype=(types.FunctionType, types.MethodType)),
          # Positional arguments, a sequence
          'args': AttrType(
            default_value=[],
            pytype=list),
          # Keyword arguments, a map
          'kargs': AttrType(
            default_value={},
            pytype=dict),
          },
        results_type={
          'retval': AttrType(
            none_allowed=True),
          })
    Registry.get_singleton().transition_types.register(cls.__type)

  def realize_impl(self):
    f = self.instr_attrs['function']
    a = self.instr_attrs['args']
    k = self.instr_attrs['kargs']
    retval = f(*a, **k)
    return { 'retval': retval, }

def register():
  PythonCode.register()

