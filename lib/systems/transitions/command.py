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
            # Node means keyboard input is possible.
            none_allowed=True,
            # str so we needn't bother with encodings
            pytype=str),
          'unless': AttrType(
            none_allowed=True,
            valid_condition=cls.is_valid_cmdline),
          'cwd': AttrType(
            none_allowed=True,
            pytype=str),
          'username': AttrType(
            none_allowed=True,
            # Commented since some users are created after validation.
            # Passing User deps would be better.
            #valid_condition=cls.is_valid_username,
            pytype=str),
          'extra_env': AttrType(
            none_allowed=True,
            valid_condition=cls.is_valid_extra_env),
          'redir_stdout': AttrType(
            default_value=False,
            pytype=bool),
          'expected_retcodes': AttrType(
            default_value=(0, ),
            valid_condition=cls.is_valid_expected_retcodes),
          },
        results_type={
          'retcode': AttrType(
            pytype=int,
            ),
          'stdout': AttrType(
            pytype=str,
            default_value='',
            ),
          })
    Registry.get_singleton().transition_types.register(cls.__restype)

  @classmethod
  def is_valid_username(cls, username):
    try:
      pwd.getpwnam(username)
    except KeyError:
      return False
    else:
      return True

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
  def is_valid_expected_retcodes(cls, expected_retcodes):
    if len(expected_retcodes) < 1:
      return False
    for retcode in expected_retcodes:
      if not isinstance(retcode, int):
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

  def realize_impl(self):
    env = self.env_with(self.instr_attrs['extra_env'])
    preexec_fn = self.dropprivs_fn(self.instr_attrs['username'])
    cwd = self.instr_attrs['cwd']

    if self.instr_attrs['unless'] is not None:
      # Remember, 0 means success
      if subprocess.call(
          self.instr_attrs['unless'],
          preexec_fn=preexec_fn,
          cwd=cwd,
          env=env) == 0:
        return {
            'retcode': 0,
            'stdout': '',
            }

    if self.instr_attrs['cmdline_input'] is None:
      stdin_flag = None
    else:
      stdin_flag = subprocess.PIPE

    if self.instr_attrs['redir_stdout']:
      stdout_flag = subprocess.PIPE
    else:
      stdout_flag = None

    p = subprocess.Popen(
        self.instr_attrs['cmdline'],
        stdin=stdin_flag,
        stdout=stdout_flag,
        preexec_fn=preexec_fn,
        cwd=cwd,
        env=env)

    # Writes, waits until completion.
    stdoutdata, stderrdata = p.communicate(self.instr_attrs['cmdline_input'])

    if stdoutdata is None:
      # redir_stdout is False
      stdoutdata = ''

    if p.returncode not in self.instr_attrs['expected_retcodes']:
      raise subprocess.CalledProcessError(
          p.returncode, self.instr_attrs['cmdline'])
    return {
        'retcode': p.returncode,
        'stdout': stdoutdata,
        }

def register():
  Command.register()

