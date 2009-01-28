# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import cStringIO as StringIO
import os
import pwd
import subprocess

from systems.registry import Registry
from systems.transition import Transition
from systems.typesystem import Type, AttrType
from systems.util.uid import drop_privs_permanently

__all__ = ('register', )

class Command(Transition):
  """
  A transition, handled via a command.

  Either the command is idempotent, or it is guarded by an 'unless'
  condition.
  """

  @classmethod
  def register(cls):
    cls.__restype = Type('Command', cls,
      [
      AttrType('name',
        identifying=True),
      AttrType('cmdline',
        valid_condition=cls.is_valid_cmdline),
      AttrType('cmdline_input',
        default_to_none=True,
        valid_condition=cls.is_valid_input),
      AttrType('unless',
        default_to_none=True,
        valid_condition=cls.is_valid_unless),
      AttrType('username',
        default_to_none=True,
        valid_condition=cls.is_valid_username),
      AttrType('extra_env',
        default_to_none=True,
        valid_condition=cls.is_valid_extra_env),
    ])
    Registry.get_singleton().transition_types.register(cls.__restype)

  @classmethod
  def is_valid_cmdline(cls, cmdline):
    return isinstance(cmdline, list)

  @classmethod
  def is_valid_extra_env(cls, extra_env):
    return extra_env is None or isinstance(extra_env, dict)

  @classmethod
  def is_valid_input(cls, input):
    # So we needn't bother with encodings
    return input is None or isinstance(input, str)

  @classmethod
  def is_valid_unless(cls, unless):
    return unless is None or cls.is_valid_cmdline(unless)

  @classmethod
  def is_valid_username(cls, username):
    return username is None or isinstance(username, str)

  @classmethod
  def env_with(cls, extra_env):
    if extra_env is None:
      return None
    env = dict(os.environ)
    env.update(extra_env)
    return env

  @classmethod
  def dropprivs_fn(cls, username):
    if username is None:
      return None
    def fn():
      pw_ent = pwd.getpwnam(username)
      drop_privs_permanently(uid=pw_ent.pw_uid, gid=pw_ent.pw_gid)
    return fn

  def realize(self):
    env = self.env_with(self.attributes['extra_env'])
    preexec_fn = self.dropprivs_fn(self.attributes['username'])

    if self.attributes['unless'] is not None:
      if subprocess.call(
          self.attributes['unless'],
          preexec_fn=preexec_fn,
          env=env):
        return

    inf = None
    if self.attributes['cmdline_input'] is not None:
      inf = StringIO.StringIO(self.attributes['cmdline_input'])
    try:
      subprocess.check_call(
          self.attributes['cmdline'],
          stdin=inf,
          preexec_fn=preexec_fn,
          env=env)
    finally:
      if inf is not None:
        inf.close()

def register():
  Command.register()

