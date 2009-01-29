# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import os
import pwd
import re
import subprocess

from systems.registry import Registry
from systems.realizable import Resource
from systems.typesystem import Type, AttrType

__all__ = ('register', )

class User(Resource):
  """
  A system user managed on the local system (/etc/password and friends)

  Uses the debian command adduser
  """

  @classmethod
  def register(cls):
    cls.__restype = Type('User', cls,
      [
      AttrType('name',
        identifying=True,
        valid_condition=cls.is_valid_username),
      AttrType('state',
        default_value='present',
        valid_condition=cls.is_valid_state),
      AttrType('home',
        default_to_none=True,
        valid_condition=cls.is_valid_home),
      AttrType('shell',
        default_to_none=True,
        valid_condition=cls.is_valid_shell),
    ])
    Registry.get_singleton().resource_types.register(cls.__restype)

  @classmethod
  def is_valid_username(cls, name):
    # from man useradd
    return bool(re.match('^[a-z_][a-z0-9_-]*[$]?$', name))

  @classmethod
  def is_valid_state(cls, state):
    return state in ('present', 'absent', )

  @classmethod
  def is_valid_home(cls, home):
    return home is None or bool(re.match('^/[/a-z0-9_-]*$', home))

  @classmethod
  def is_valid_shell(cls, shell):
    return shell is None or bool(re.match('^/[/a-z0-9_-]*$', shell))

  def read_state(self):
    name = self.attributes['name']
    try:
      p = pwd.getpwnam(name)
    except KeyError:
      state = 'absent'
      home = None
      shell = None
    else:
      state = 'present'
      home = p.pw_dir
      shell = p.pw_shell
    return {
        'name': name,
        'state': state,
        'home': home,
        'shell': shell,
        }

  def realize(self):
    state0 = self.read_state()
    state1 = self.attributes
    if state0 == state1:
      return

    s0, s1 = state0['state'], state1['state']
    if (s0, s1) == ('absent', 'absent'):
      return
    elif (s0, s1) == ('present', 'present'):
      cmd = ['/usr/sbin/usermod', ]
    elif (s0, s1) == ('absent', 'present'):
      cmd = ['/usr/sbin/adduser', '--system', '--disabled-password', ]
    elif (s0, s1) == ('present', 'absent'):
      cmd = ['/usr/sbin/deluser', ]
    else:
      assert False

    if s1 == 'present':
      if self.attributes['home'] is not None:
        cmd.extend(['--home', self.attributes['home']])
      if self.attributes['shell'] is not None:
        cmd.extend(['--shell', self.attributes['shell']])

    cmd.extend(['--', self.attributes['name']])
    subprocess.check_call(cmd)

def register():
  User.register()

