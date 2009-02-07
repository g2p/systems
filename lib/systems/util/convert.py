# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

def oct_to_int(octa):
  """
  Convert an octal string to an integer.
  """

  if not isinstance(octa, str):
    raise TypeError
  return int(octa, 8)

def int_to_oct(intgr):
  """
  Convert an integer to a 0-started octal string.

  Not using the oct builtin because its output changed in python 3.0.
  """

  if not isinstance(intgr, int):
    raise TypeError(intgr, int)
  if intgr < 0:
    raise ValueError(intgr)
  octa = ''
  while intgr > 0:
    intgr, mod = divmod(intgr, 8)
    octa = str(mod) + octa
  return '0' + octa


