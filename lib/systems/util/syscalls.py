# vim: set fileencoding=utf-8 sw=2 ts=2 et :

import ctypes
import os

# There is a portability issue with the sizes of mode_t and uid_t.
# Having those in ctypes would be great.
# Otherwise, Cython could help, but may be overkill right now.
_libc = ctypes.cdll.LoadLibrary(None)
_errno = ctypes.c_int.in_dll(_libc, 'errno')

def fchmod(fd, mode):
  # To get sizes: gcc -D_GNU_SOURCE -E /usr/include/sys/stat.h -o sysstat.i
  fd = ctypes.c_int(fd)
  mode = ctypes.c_uint(mode)
  res = _libc.fchmod(fd, mode)
  if res:
    raise OSError(_errno.value, os.strerror(_errno.value))

