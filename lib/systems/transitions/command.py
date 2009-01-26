# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import subprocess
import cStringIO as StringIO

from systems.registry import Registry
from systems.transition import Transition
from systems.typesystem import Type, AttrType

__all__ = ('register', )

class Command(Transition):
  """
  A transition, handled via a command.

  Either the command is idempotent, or it is guarded by an 'unless'
  condition.

  XXX Validate for arrays I guess
  """

  @classmethod
  def register(cls):
    cls.__restype = Type('Command', cls,
      [
      AttrType('name',
        identifying=True),
      AttrType('cmdline',
        valid_condition=cls.is_valid_cmdline),
      AttrType('input',
        default_to_none=True,
        valid_condition=cls.is_valid_input),
      AttrType('unless',
        default_to_none=True,
        valid_condition=cls.is_valid_unless),
    ])
    Registry.get_singleton().transition_types.register(cls.__restype)

  @classmethod
  def is_valid_cmdline(cls, cmdline):
    return isinstance(cmdline, list)

  @classmethod
  def is_valid_input(cls, input):
    # So we needn't bother with encodings
    return input is None or isinstance(input, str)

  @classmethod
  def is_valid_unless(cls, unless):
    return unless is None or cls.is_valid_cmdline(unless)

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

