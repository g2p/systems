# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from __future__ import with_statement
import sys

import systems.context
import systems.transitions
from systems.util.templates import build_and_render
from systems.realizable_dsl import \
    ensure_transition, ref_transition, ensure_anon

systems.transitions.register()
gc = systems.context.global_context()

ensure_transition('Command',
    name='foo', cmdline=['/bin/echo', 'Chatty command is chatty'])

ensure_transition('PythonCode', name='fariboles',
    function=lambda: sys.stderr.write('Fariboles!\n'))

ensure_transition('File',
    path='/tmp/testfile',
    mode=0644,
    contents=build_and_render(
      'Hello {{ name }}!\n',
      name='Jane Doe') \
          .encode('utf8'))

r1 = ensure_transition('AptitudePackage',
    name='python-networkx')

r2 = ensure_transition('User',
    name='zorglub', state='absent', shell='/bin/true')

ensure_anon(depends=(r1, r2))

def test_gitosis(pub_file, user_name='git', user_home='/var/git'):
  ensure_transition('AptitudePackage',
      name='gitosis')

  user = ensure_transition('User',
      name=user_name, home=user_home, shell='/bin/sh')

  with open(pub_file) as f:
    pub_file_s = f.read()

  ensure_transition('Command',
      name='setup-gitosis',
      username=user_name,
      extra_env={'HOME': user_home, },
      cmdline=['/usr/bin/gitosis-init', ],
      cmdline_input=pub_file_s,
      unless=[
        '/usr/bin/test', '-f', user_home+'/.gitosis.conf'],
      depends=[
        ref_transition('AptitudePackage', name='gitosis'),
        ref_transition('User', name=user_name)])
test_gitosis('g2p-moulinex.pub')

c = ensure_transition('PgCluster')
u = ensure_transition('PgUser', cluster=c, name='user-pfuuit')
d = ensure_transition('PgDatabase', user=u, name='db-pfuuit')
b = ensure_transition('PgDbBackup', database=d)

gc.realize()

