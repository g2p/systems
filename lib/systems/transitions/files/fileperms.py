# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

# use posixpath for platform-indepent paths
import grp
import os
import pwd
import stat

from systems.dsl import transition
from systems.util.convert import int_to_oct, oct_to_int


def is_valid_path(path):
  """
  Only absolute paths are accepted.
  """

  return os.path.isabs(path)

def is_valid_username(username):
  try:
    pwd.getpwnam(username)
  except KeyError:
    return False
  else:
    return True

def is_valid_groupname(groupname):
  try:
    grp.getgrnam(groupname)
  except KeyError:
    return False
  else:
    return True

def read_present(id_attrs, kind_test):
  """
  Whether the file exists and has the desired kind.

  kind_test is something like stat.S_ISDIR
  """

  assert kind_test in (stat.S_ISDIR, stat.S_ISREG, stat.S_ISLNK, )

  path = id_attrs['path']
  try:
    st = os.lstat(path)
  except OSError:
    # Does not exist
    return False
  else:
    # True iff correct kind
    return bool(kind_test(st.st_mode))

def is_valid_mode(mode):
  mode = oct_to_int(mode)
  # Only allow the permission bits and suid stuff.
  return mode == stat.S_IMODE(mode)

def read_owner(id_attrs):
  path = id_attrs['path']
  return pwd.getpwuid(os.lstat(path).st_uid).pw_name

def read_group(id_attrs):
  path = id_attrs['path']
  return grp.getgrgid(os.lstat(path).st_gid).gr_name

def read_mode(id_attrs):
  path = id_attrs['path']
  return int_to_oct(stat.S_IMODE(os.lstat(path).st_mode))



class FilePermsMixin(object):
  """
  Mixin for plain files, directories and symlinks.
  """

  def fp_expand_into(self, rg):
    code = transition('PythonCode', function=self._realize)
    code = rg.add_transition(code)

  def _realize(self):
    # We should pass around file-descriptors to be safe.
    present0 = self.read_attrs()['present']
    present1 = self.wanted_attrs['present']

    if present1:
      if not present0:
        # Don't let files be accessible between creation and permission setting.
        u = os.umask(0777)
        self.create()
        os.umask(u)
      self.realize_perms()
      self.update()
    elif present0:
      self.delete()

  def create(self):
    raise NotImplementedError

  def update(self):
    raise NotImplementedError

  def delete(self):
    raise NotImplementedError

  def realize_perms(self):
    path = self.id_attrs['path']

    # Order is important. First lchown then lchmod.
    owner = self.wanted_attrs['owner']
    group = self.wanted_attrs['group']
    if owner is not None:
      uid = pwd.getpwnam(owner).pw_uid
    else:
      uid = -1
    if group is not None:
      gid = grp.getgrnam(group).gr_gid
    else:
      gid = -1
    # -1 means no change
    os.lchown(path, uid, gid)

    # XXX if we handle symlinks, need to wrap lchmod.
    os.chmod(path, oct_to_int(self.wanted_attrs['mode']))


