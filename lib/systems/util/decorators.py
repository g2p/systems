# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import sys

__all__ = ('propget', 'propset', 'propdel', )

def propget(func):
  locs = sys._getframe(1).f_locals
  name = func.__name__
  prop = locs.get(name)
  if not isinstance(prop, property):
    prop = property(func, doc=func.__doc__)
  else:
    doc = prop.__doc__ or func.__doc__
    prop = property(func, prop.fset, prop.fdel, doc=doc)
  return prop

def propset(func):
  locs = sys._getframe(1).f_locals
  name = func.__name__
  prop = locs.get(name)
  if not isinstance(prop, property):
    prop = property(None, func, doc=func.__doc__)
  else:
    doc = prop.__doc__ or func.__doc__
    prop = property(prop.fget, func, prop.fdel, doc=doc)
  return prop

def propdel(func):
  locs = sys._getframe(1).f_locals
  name = func.__name__
  prop = locs.get(name)
  if not isinstance(prop, property):
    prop = property(None, None, func, doc=func.__doc__)
  else:
    prop = property(prop.fget, prop.fset, func, doc=prop.__doc__)
  return prop

class memoized(object):
  """
  Decorator that caches a function's return value each time it is called.

  If called later with the same arguments,
  the cached value is returned, and not re-evaluated.
  """

  def __init__(self, func):
    self.func = func
    self.__doc__ = func.__doc__
    self.__name__ = func.__name__
    self.cache = {}

  def __call__(self, *args):
    try:
      return self.cache[args]
    except KeyError:
      self.cache[args] = value = self.func(*args)
      return value

