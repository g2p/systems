# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import types

"""
Precondition support.

Decorators aren't enough, because we need to play nice
with inheritance too. There is also a metaclass, and a
base class that plugs the metaclass.

Preconditions throw exceptions if they aren't satisfied.

Throwing is more convenient than using a return value,
because backtraces will show the exact source of the problem.
"""

__all__ = ('ContractSupportBase', 'precondition', )


def wrap(checked_fn, precond_fns):
  """
  Wraps a function and its preconditions.

  This couldn't be implemented with callable objects,
  because that would hijack the 'self' argument.
  """

  def with_checks(self, *args, **kargs):
    for precond_fn in precond_fns:
      precond_fn(self, *args, **kargs)
    return checked_fn(self, *args, **kargs)
  with_checks._func = checked_fn
  with_checks._preconds = precond_fns
  with_checks._is_a_wrapped_function = None
  with_checks.__name__ = checked_fn.__name__
  with_checks.__doc__ = checked_fn.__doc__
  return with_checks


def is_wrapped(func):
  return hasattr(func, '_is_a_wrapped_function')


class MultipleInheritancePathsError(Exception):
  """
  Thrown when a contract-related method is inherited through
  different base classes.
  """

  pass


class ContractSupportMcls(type):
  """
  This metaclass does magic so that when you override
  a method that has preconditions, the preconditions
  still apply.

  It will refuse ambiguous cases, such as inheriting a method
  through different paths. This is so we don't have to decide
  which of the base preconditions we should keep.
  """

  def __new__(mcls, name, bases, dct):
    attrnames = set()
    for base in bases:
      for attrname in vars(base):
        base_attr = getattr(base, attrname)
        if isinstance(base_attr, types.MethodType):
          base_func = base_attr.im_func
          if is_wrapped(base_func):
            attrnames.add(attrname)
    for attrname in dct:
      attr = dct[attrname]
      if is_wrapped(attr):
        attrnames.add(attrname)
    for attrname in attrnames:
      # Use a set so that unambiguous multi-path inheritance works.
      base_attrs = set(getattr(base, attrname)
          for base in bases if hasattr(base, attrname))
      if len(base_attrs) > 1:
        raise MultipleInheritancePathsError(base_attrs)
      base_fwc = None
      for base_attr in base_attrs:
        if isinstance(base_attr, types.MethodType):
          base_func = base_attr.im_func
          if is_wrapped(base_func):
            base_fwc = base_func
      fwc = None
      func = None
      if attrname in dct:
        func = dct[attrname]
        if is_wrapped(func):
          fwc = func
      if base_fwc is not None:
        if fwc is not None:
          dct[attrname] = wrap(fwc._func, base_fwc._preconds + fwc._preconds)
        elif func is not None:
          dct[attrname] = wrap(func, base_fwc._preconds)
    return type.__new__(mcls, name, bases, dct)


class ContractSupportBase(object):
  """
  Inherit from this class so that preconditions on methods
  are still applied to overriding methods.
  """

  __metaclass__ = ContractSupportMcls


def precondition(precond_fn):
  """
  Usage:
  class foo(ContractSupportBase):
    def _precond(self, foo):
      if foo < 0:
        raise ValueError
    @precondition(_precond)
    def method(self):
      pass
  """

  def partial_application(checked_fn):
    return wrap(checked_fn, [precond_fn])
  return partial_application


