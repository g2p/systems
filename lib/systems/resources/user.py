# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import os
import re
import subprocess

from systems.registry import Registry
from systems.resource import Resource
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

  def get_state(self):
    # Should implement subprocess.NULL (also called IGNORE on the mlist)
    # Use os.devnull (:NUL on windows). subprocess.CLOSED has no fans.
    with open(os.devnull, 'w') as nullf:
      r = subprocess.call(
          ['/usr/bin/id', '-u', '--', self.attributes['name']],
          stderr=nullf)
    if r != 0:
      return 'absent'
    else:
      return 'present'

  def realize(self):
    if self.get_state() == self.attributes['state']:
      return #XXX — shell and home may need to be changed

    print self.attributes['state']
    if self.attributes['state'] == 'present':
      cmd = ['/usr/sbin/adduser', '--system', '--disabled-password', ]
      if self.attributes['home'] is not None:
        cmd.extend(['--home', self.attributes['home']])
      if self.attributes['shell'] is not None:
        cmd.extend(['--shell', self.attributes['shell']])
    else:
      cmd = ['/usr/sbin/deluser', ]
    cmd.extend(['--', self.attributes['name']])
    subprocess.check_call(cmd)

def register():
  User.register()

