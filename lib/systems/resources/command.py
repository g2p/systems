# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import subprocess
import cStringIO as StringIO

from systems.registry import Registry
from systems.resource import Resource, ResourceType, ResourceAttr

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
      ResourceAttr('input',
        identifying=False, naming=False, default_to_none=True),
      ResourceAttr('unless',
        identifying=False, naming=False, default_to_none=True),
    ])
    Registry.get_singleton().resource_types.register(cls.__restype)

  @classmethod
  def is_valid_input(cls, input):
    # So we needn't bother with encodings
    return input is None or isinstance(input, str)

  def realize(self):
    if self.attributes['unless'] is not None \
        and subprocess.call(self.attributes['unless']):
          return

    inf = None
    if self.attributes['input'] is not None:
      inf = StringIO.StringIO(self.attributes['input'])
    try:
      subprocess.check_call(self.attributes['cmdline'], stdin=inf)
    finally:
      if inf is not None:
        inf.close()

def register():
  Command.register()

