# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import with_statement
import sys

import systems.context
import systems.transitions
from systems.dsl import resource, transition
from systems.util.templates import build_and_render

gc = systems.context.global_context()
systems.transitions.register()

t1 = transition('Command',
    cmdline=['/bin/echo', 'Chatty command is chatty'])
t2 = transition('PythonCode',
    function=lambda: sys.stderr.write('Fariboles!\n'))
gc.ensure_transition(t1)
gc.ensure_transition(t2)

text = build_and_render('Hello {{ name }}!\n', name='Jane Doe')

ensure_resource(gc, 'File',
    path='/tmp/testfile',
    mode=0644,
    contents=text.encode('utf8'))
ensure_resource(gc, 'AptitudePackage', name='python-networkx')
ensure_resource(gc, 'User',
    name='zorglub', state='absent', shell='/bin/true')

c = ensure_resource(gc, 'PgCluster')
u = ensure_resource(gc, 'PgUser', cluster=c, name='user-pfuuit')
d = ensure_resource(gc, 'PgDatabase', user=u, name='db-pfuuit')
b = ensure_resource(gc, 'PgDbBackup', database=d)

def test_gitosis(pub_file, user_name='git', user_home='/var/git'):
  ensure_resource(gc, 'AptitudePackage', name='gitosis')

  ensure_resource(gc, 'User',
      name=user_name, home=user_home, shell='/bin/sh')

  with open(pub_file) as f:
    pub_file_s = f.read()

  cmd = transition('Command',
      username=user_name,
      extra_env={'HOME': user_home, },
      cmdline=['/usr/bin/gitosis-init', ],
      cmdline_input=pub_file_s,
      unless=[
        '/usr/bin/test', '-f', user_home+'/.gitosis.conf'],
      )
  # XXX Need mixed resource/transition depends.
  # Maybe put sentinels to represent resources in the transition graph,
  # and put all depends in this graph.
  gc.ensure_transition(cmd)
test_gitosis('g2p-moulinex.pub')

gc.realize()

