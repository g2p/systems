# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import cStringIO as StringIO
import os
import pwd
import subprocess

from systems.registry import Registry
from systems.realizable import Transition
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
        none_allowed=True,
        # So we needn't bother with encodings
        pytype=str),
      AttrType('unless',
        none_allowed=True,
        valid_condition=cls.is_valid_cmdline),
      AttrType('username',
        none_allowed=True,
        pytype=str),
      AttrType('extra_env',
        none_allowed=True,
        valid_condition=cls.is_valid_extra_env),
    ])
    Registry.get_singleton().transition_types.register(cls.__restype)

  @classmethod
  def is_valid_cmdline(cls, cmdline):
    if not isinstance(cmdline, list):
      return False
    for e in cmdline:
      if not isinstance(e, str):
        return False
    return True

  @classmethod
  def is_valid_extra_env(cls, extra_env):
    if not isinstance(extra_env, dict):
      return False
    for (k, v) in extra_env.iteritems():
      if not isinstance(k, str):
        return False
      if not isinstance(v, str):
        return False
    return True

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
      # Remember, 0 means success
      if subprocess.call(
          self.attributes['unless'],
          preexec_fn=preexec_fn,
          env=env) == 0:
        return

    if self.attributes['cmdline_input'] is None:
      # Let stdin pass through
      input_flag = None
    else:
      # We have a string to write
      input_flag = subprocess.PIPE
    p = subprocess.Popen(
        self.attributes['cmdline'],
        stdin=input_flag,
        preexec_fn=preexec_fn,
        env=env)
    # Input may safely be None. Writes, waits until completion.
    p.communicate(self.attributes['cmdline_input'])
    if p.returncode != 0:
      raise subprocess.CalledProcessError(
          p.returncode, self.attributes['cmdline'])

def register():
  Command.register()

