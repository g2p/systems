# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import os
import pwd
import re
import subprocess

from systems.dsl import transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource, Attrs

__all__ = ('register', )

class User(Resource):
  """
  A system user managed on the local system (/etc/password and friends)

  Uses the debian command adduser
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('User', cls,
        id_type={
          'name': AttrType(
            valid_condition=cls.is_valid_username),
          },
        state_type={
          'present': AttrType(
            default_value=True,
            pytype=bool),
          'home': AttrType(
            none_allowed=True,
            valid_condition=cls.is_valid_home),
          'shell': AttrType(
            none_allowed=True,
            valid_condition=cls.is_valid_shell),
          })
    Registry.get_singleton().resource_types.register(cls.__restype)

  @classmethod
  def is_valid_username(cls, name):
    # from man useradd
    return bool(re.match('^[a-z_][a-z0-9_-]*[$]?$', name))

  @classmethod
  def is_valid_home(cls, home):
    return home is None or bool(re.match('^/[/a-z0-9_-]*$', home))

  @classmethod
  def is_valid_shell(cls, shell):
    return shell is None or bool(re.match('^/[/a-z0-9_-]*$', shell))

  def _read_attrs(self):
    name = self.id_attrs['name']
    try:
      p = pwd.getpwnam(name)
    except KeyError:
      present = False
      home = None
      shell = None
    else:
      present = True
      home = p.pw_dir
      shell = p.pw_shell
    return {
        'present': present,
        'home': home,
        'shell': shell,
        }

  def expand_into(self, rg):
    state0 = self.read_attrs()
    state1 = self.wanted_attrs
    if state0 == state1:
      return

    p0, p1 = state0['present'], state1['present']
    if (p0, p1) == (False, False):
      return
    elif (p0, p1) == (True, True):
      cmdline = ['/usr/sbin/usermod', ]
    elif (p0, p1) == (False, True):
      cmdline = ['/usr/sbin/adduser', '--system', '--disabled-password', ]
    elif (p0, p1) == (True, False):
      cmdline = ['/usr/sbin/deluser', ]
    else:
      assert False

    if p1:
      if self.wanted_attrs['home'] is not None:
        cmdline.extend(['--home', self.wanted_attrs['home']])
      if self.wanted_attrs['shell'] is not None:
        cmdline.extend(['--shell', self.wanted_attrs['shell']])

    cmdline.extend(['--', self.id_attrs['name']])
    cmd = transition('Command', cmdline=cmdline)
    rg.add_transition(cmd)

def register():
  User.register()

