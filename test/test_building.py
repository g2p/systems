# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import
from __future__ import with_statement

import sys
import logging

# Set up a default handler that writes to stderr.
logging.basicConfig(level=logging.DEBUG)

import systems.context
import systems.transitions
from systems.dsl import resource, ensure_resource, ensure_transition
from systems.util.templates import build_and_render

gc = systems.context.global_context()
systems.transitions.register()

cluster = ensure_resource(gc, 'PgCluster')
rails_sites = ensure_resource(gc, 'Directory',
    path='/var/lib/rails-sites', mode='0755')
redmine = ensure_resource(gc, 'Redmine',
    name='main',
    path='/var/lib/rails-sites/redmine',
    cluster=cluster,
    depends=[rails_sites])

ensure_transition(gc, 'Command',
    cmdline=['/bin/echo', 'Chatty command is chatty'])
ensure_transition(gc, 'PythonCode',
    function=lambda: sys.stderr.write('Fariboles!\n'))

text = build_and_render('Hello {{ name }}!\n', name='Jane Doe')

ensure_resource(gc, 'PlainFile',
    path='/tmp/testfile',
    mode='0644',
    contents=text.encode('utf8'))
ensure_resource(gc, 'AptitudePackage', name='python-networkx')
ensure_resource(gc, 'User',
    name='zorglub', present=False, shell='/bin/true')

u = ensure_resource(gc, 'PgUser', name='user-pfuuit', cluster=cluster)
d = ensure_resource(gc, 'PgDatabase',
    owner=u, name='db-pfuuit', cluster=cluster)

if False:
  ensure_resource(gc, 'SvnWorkingCopy',
    location=resource('Directory',
      path='/tmp/django-queue-service',
      mode='0755',
      owner='nobody',
      group='nogroup'),
    url='http://django-queue-service.googlecode.com/svn/trunk/')

def test_gitosis(pub_file, user_name='git', user_home='/var/git'):
  with open(pub_file) as f:
    pub_file_s = f.read()

  pkg = ensure_resource(gc, 'AptitudePackage', name='gitosis')

  usr = ensure_resource(gc, 'User',
      name=user_name, home=user_home, shell='/bin/sh')

  ensure_transition(gc, 'Command',
      username=user_name,
      extra_env={'HOME': user_home, },
      cmdline=['/usr/bin/gitosis-init', ],
      cmdline_input=pub_file_s,
      unless=[
        '/usr/bin/test', '-f', user_home+'/.gitosis.conf'],
      depends=(pkg, usr)
      )

#test_gitosis('g2p-moulinex.pub')

gc.realize()

