# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import
from __future__ import with_statement

import sys
import logging
import runpy

# Set up a default handler that writes to stderr.
logging.basicConfig(level=logging.DEBUG)

from systems.context import Realizer
from systems.dsl import resource, transition
from systems.typesystem import FunExpandable
from systems.util.templates import build_and_render

runpy.run_module('systems.transitions.__init__')['register']()

def run_tests(rg):
  cluster = rg.add_resource(resource('PgCluster'))
  rails_sites = rg.add_resource(resource('Directory',
      path='/var/lib/rails-sites', mode='0755'))
  redmine = rg.add_resource(resource('Redmine',
        name='main',
        path='/var/lib/rails-sites/redmine',
        cluster=cluster.ref(rg),
        ),
      depends=[rails_sites],
      )

  rg.add_transition(transition('Command',
      cmdline=['/bin/echo', 'Chatty command is chatty']))
  rg.add_transition(transition('PythonCode',
      function=lambda: sys.stderr.write('Fariboles!\n')))

  text = build_and_render('Hello {{ name }}!\n', name='Jane Doe')

  rg.add_resource(resource('PlainFile',
      path='/tmp/testfile',
      mode='0644',
      contents=text.encode('utf8')))
  rg.add_resource(resource('AptitudePackage', name='python-networkx'))
  rg.add_resource(resource('User',
      name='zorglub', present=False, shell='/bin/true'))

  u = rg.add_resource(resource('PgUser', name='user-pfuuit', cluster=cluster.ref(rg)))
  d = rg.add_resource(resource('PgDatabase',
      owner=u.ref(rg), name='db-pfuuit', cluster=cluster.ref(rg)))

  if False:
    rg.add_resource(resource('SvnWorkingCopy',
      location=resource('Directory',
        path='/tmp/django-queue-service',
        mode='0755',
        owner='nobody',
        group='nogroup'),
      url='http://django-queue-service.googlecode.com/svn/trunk/'))

  def test_gitosis(pub_file, user_name='git', user_home='/var/git'):
    with open(pub_file) as f:
      pub_file_s = f.read()

    pkg = rg.add_resource(resource('AptitudePackage', name='gitosis'))

    usr = rg.add_resource(resource('User',
        name=user_name, home=user_home, shell='/bin/sh'))

    rg.add_transition(transition('Command',
        username=user_name,
        extra_env={'HOME': user_home, },
        cmdline=['/usr/bin/gitosis-init', ],
        cmdline_input=pub_file_s,
        unless=[
          '/usr/bin/test', '-f', user_home+'/.gitosis.conf'],
        ),
      depends=(pkg, usr),
      )

  #test_gitosis('g2p-moulinex.pub')

Realizer(FunExpandable(run_tests)).realize()


