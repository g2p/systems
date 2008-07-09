from __future__ import with_statement
import os
import re
import subprocess

from registry import Registry
from resource import Resource, ResourceType, ResourceAttr

__all__ = ('User', )

class User(Resource):
  """
  A user managed on the local system (/etc/password and friends)

  Uses the debian command adduser
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('User', cls,
      [
      ResourceAttr('name',
        identifying=True, naming=True),
      ResourceAttr('state',
        identifying=False, naming=False, default_value='present'),
    ])
    Registry.get_singleton().register_resource_type(cls.__restype)

  @classmethod
  def is_valid_username(cls, name):
    # from man useradd
    return bool(re.match('^[a-z_][a-z0-9_-]*[$]?$', name))

  @classmethod
  def is_valid_state(cls, state):
    return state in ('present', 'absent', )

  def _check_valdict(self):
    """
    Extra checks.
    """

    if not self.is_valid_username(self.attributes['name']):
      raise ValueError('Not a valid user name')
    if not self.is_valid_state(self.attributes['state']):
      raise ValueError('Not a valid user state')

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
      return

    print self.attributes['state']
    if self.attributes['state'] == 'present':
      subprocess.check_call(['/usr/sbin/adduser', '--system',
        '--', self.attributes['name']])
    else:
      subprocess.check_call(['/usr/sbin/deluser',
        '--', self.attributes['name']])

def register():
  User.register()

# vim: set sw=2 ts=2 et :
