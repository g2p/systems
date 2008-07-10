from __future__ import with_statement
import subprocess

from registry import Registry
from resource import Resource, ResourceType, ResourceAttr

__all__ = ('register', )

class Command(Resource):
  """
  A resource, handled via a command.

  Either the command is idempotent, or it is guarded by an 'unless'
  condition.

  XXX Validate for arrays I guess
  """

  @classmethod
  def register(cls):
    cls.__restype = ResourceType('Command', cls,
      [
      ResourceAttr('name',
        identifying=True, naming=True),
      ResourceAttr('cmdline',
        identifying=False, naming=False),
      ResourceAttr('unless',
        identifying=False, naming=False, default_to_none=True),
    ])
    Registry.get_singleton().register_resource_type(cls.__restype)

  def realize(self):
    if self.attributes['unless'] is None \
        or subprocess.call(self.attributes['unless']):
      subprocess.check_call(self.attributes['cmdline'])

def register():
  Command.register()

# vim: set sw=2 ts=2 et :
