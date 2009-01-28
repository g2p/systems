# vim: set fileencoding=utf-8 sw=2 ts=2 et :

# Also see http://code.google.com/p/change-process-identity/downloads/list
# Ignore AIX and solaris ifdefs, the general case is simple.

import ctypes
import os

_libc = ctypes.cdll.LoadLibrary(None)
_errno = ctypes.c_int.in_dll(_libc, 'errno')

def getresuid():
  ruid = ctypes.c_long()
  euid = ctypes.c_long()
  suid = ctypes.c_long()
  res = _libc.getresuid(ctypes.byref(ruid), ctypes.byref(euid), ctypes.byref(suid))
  if res:
    raise OSError(_errno.value, os.strerror(_errno.value))
  return (ruid.value, euid.value, suid.value)

def setresuid(ruid=-1, euid=-1, suid=-1):
  ruid = ctypes.c_long(ruid)
  euid = ctypes.c_long(euid)
  suid = ctypes.c_long(suid)
  res = _libc.setresuid(ruid, euid, suid)
  if res:
    raise OSError(_errno.value, os.strerror(_errno.value))

def getresgid():
  rgid = ctypes.c_long()
  egid = ctypes.c_long()
  sgid = ctypes.c_long()
  res = _libc.getresgid(ctypes.byref(rgid), ctypes.byref(egid), ctypes.byref(sgid))
  if res:
    raise OSError(_errno.value, os.strerror(_errno.value))
  return (rgid.value, egid.value, sgid.value)

def setresgid(rgid=-1, egid=-1, sgid=-1):
  rgid = ctypes.c_long(rgid)
  egid = ctypes.c_long(egid)
  sgid = ctypes.c_long(sgid)
  res = _libc.setresgid(rgid, egid, sgid)
  if res:
    raise OSError(_errno.value, os.strerror(_errno.value))

def drop_privs_permanently(uid, gid):
  # -1 has special meaning and that complicates things.
  if uid < 0 or gid < 0:
    raise ValueError
  setresuid(0, 0, 0)
  setresgid(0, 0, 0)
  os.setgroups([gid])
  setresgid(gid, gid, gid)
  setresuid(uid, uid, uid)
  if getresuid() != (uid, uid, uid) \
      or getresgid() != (gid, gid, gid) \
      or os.getgroups() != [gid]:
    raise RuntimeError('Unable to drop privileges')

