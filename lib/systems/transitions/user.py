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
          'state': AttrType(
            default_value='present',
            valid_condition=cls.is_valid_state),
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
  def is_valid_state(cls, state):
    return state in ('present', 'absent', )

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
      state = 'absent'
      home = None
      shell = None
    else:
      state = 'present'
      home = p.pw_dir
      shell = p.pw_shell
    return {
        'state': state,
        'home': home,
        'shell': shell,
        }

  def place_transitions(self, transition_graph):
    state0 = self.read_attrs()
    state1 = self.wanted_attrs
    if state0 == state1:
      return

    s0, s1 = state0['state'], state1['state']
    if (s0, s1) == ('absent', 'absent'):
      return
    elif (s0, s1) == ('present', 'present'):
      cmdline = ['/usr/sbin/usermod', ]
    elif (s0, s1) == ('absent', 'present'):
      cmdline = ['/usr/sbin/adduser', '--system', '--disabled-password', ]
    elif (s0, s1) == ('present', 'absent'):
      cmdline = ['/usr/sbin/deluser', ]
    else:
      assert False

    if s1 == 'present':
      if self.wanted_attrs['home'] is not None:
        cmdline.extend(['--home', self.wanted_attrs['home']])
      if self.wanted_attrs['shell'] is not None:
        cmdline.extend(['--shell', self.wanted_attrs['shell']])

    cmdline.extend(['--', self.id_attrs['name']])
    cmd = transition('Command', cmdline=cmdline)
    transition_graph.add_transition(cmd)
    return cmd

def register():
  User.register()

