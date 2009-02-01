# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import cStringIO as StringIO
import os
import pwd
import subprocess

from systems.registry import Registry
from systems.typesystem import AttrType, TransitionType, Transition
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
    cls.__restype = TransitionType('Command', cls,
        instr_type={
          'cmdline': AttrType(
            valid_condition=cls.is_valid_cmdline),
          'cmdline_input': AttrType(
            none_allowed=True,
            # So we needn't bother with encodings
            pytype=str),
          'unless': AttrType(
            none_allowed=True,
            valid_condition=cls.is_valid_cmdline),
          'username': AttrType(
            none_allowed=True,
            pytype=str),
          'extra_env': AttrType(
            none_allowed=True,
            valid_condition=cls.is_valid_extra_env),
          },
        results_type={
          })
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
    env = self.env_with(self.instr_attrs['extra_env'])
    preexec_fn = self.dropprivs_fn(self.instr_attrs['username'])

    if self.instr_attrs['unless'] is not None:
      # Remember, 0 means success
      if subprocess.call(
          self.instr_attrs['unless'],
          preexec_fn=preexec_fn,
          env=env) == 0:
        return

    if self.instr_attrs['cmdline_input'] is None:
      # Let stdin pass through
      input_flag = None
    else:
      # We have a string to write
      input_flag = subprocess.PIPE
    p = subprocess.Popen(
        self.instr_attrs['cmdline'],
        stdin=input_flag,
        preexec_fn=preexec_fn,
        env=env)
    # Input may safely be None. Writes, waits until completion.
    p.communicate(self.instr_attrs['cmdline_input'])
    if p.returncode != 0:
      raise subprocess.CalledProcessError(
          p.returncode, self.instr_attrs['cmdline'])

def register():
  Command.register()

