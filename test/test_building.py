# vim: set fileencoding=utf-8 sw=2 ts=2 et :

from __future__ import with_statement
import sys

import systems.context
import systems.resources
import systems.transitions
from systems.util.templates import build_and_render
from systems.resource import ensure_resource, ref_resource
from systems.transition import ensure_transition
from systems.composites.postgresql.cluster import Cluster

systems.resources.register()
systems.transitions.register()
gc = systems.context.global_context()

ensure_transition('Command',
    name='foo', cmdline=['/bin/echo', 'Chatty command is chatty'])

ensure_transition('PythonCode', name='fariboles',
    function=lambda: sys.stderr.write('Fariboles!\n'))

ensure_resource('File',
    path='/tmp/testfile',
    contents=build_and_render(
      'Hello {{ name }}!\n',
      name='Jane Doe') \
          .encode('utf8'))

ensure_resource('FirstSentinel')

ensure_resource('AptitudePackage',
    name='python-networkx')

ensure_resource('User',
    name='zorglub', state='absent', shell='/bin/true')

def test_gitosis(pub_file, user_name='git', user_home='/var/git'):
  ensure_resource('AptitudePackage',
      name='gitosis')

  ensure_resource('User',
      name=user_name, home=user_home, shell='/bin/sh')

  with open(pub_file) as f:
    pub_file_s = f.read()
  ensure_transition('Command',
      name='setup-gitosis',
      cmdline=[
        '/usr/bin/sudo', '-H', '-u', user_name,
        '/usr/bin/gitosis-init'],
      cmdline_input=pub_file_s,
      unless=[
        '/usr/bin/test', '-f', user_home+'/.gitosis.conf'],
      depends=[
        ref_resource('AptitudePackage', name='gitosis'),
        ref_resource('User', name=user_name)])
test_gitosis('g2p-moulinex.pub')

c = Cluster()
c.ensure_create_user(gc, 'user_pfuuit')
c.ensure_create_database(gc, 'db_pfuuit', 'user_pfuuit')

gc.realize()

