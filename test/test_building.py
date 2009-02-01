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
f = resource('File',
    path='/tmp/testfile',
    mode=0644,
    contents=text.encode('utf8'))
p = resource('AptitudePackage', name='python-networkx')
u = resource('User',
    name='zorglub', state='absent', shell='/bin/true')

gc.ensure_resource(p)
gc.ensure_resource(f)
gc.ensure_resource(u)

c = resource('PgCluster')
u = resource('PgUser', cluster=c, name='user-pfuuit')
d = resource('PgDatabase', user=u, name='db-pfuuit')
b = resource('PgDbBackup', database=d)

gc.ensure_resource(c)
gc.ensure_resource(u)
gc.ensure_resource(d)
gc.ensure_resource(b)


def test_gitosis(pub_file, user_name='git', user_home='/var/git'):
  pkg = resource('AptitudePackage', name='gitosis')

  user = resource('User',
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
  gc.ensure_resource(pkg)
  gc.ensure_resource(user)
  gc.ensure_transition(cmd)
test_gitosis('g2p-moulinex.pub')

gc.realize()

