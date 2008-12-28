import jinja2

from resource import ensure_resource, ref_resource
from context import global_context

import resources
resources.register()

# XXX Need to also test error checking; write scripts that fail.

ensure_resource('User',
    name='zorglub', state='absent')

ensure_resource('Command',
    name='foo', cmdline=['/bin/echo', '434'])

template = jinja2.Template('Hello {{ whomever }}!\n')

ensure_resource('File',
    path='/tmp/testfile',
    contents=template.render(name='Jane Doe').encode('utf8'))

def test_gitosis(pub_file, user_name='git', user_home='/var/git'):
  ensure_resource('AptitudePackage',
      name='gitosis')

  ensure_resource('User',
      name=user_name, home=user_home, shell='/bin/sh')

  # pub file is used unquoted in an sh line
  ensure_resource('Command',
      name='setup-gitosis',
      cmdline=[
        '/usr/bin/sudo', '-H', '-u', user_name, 'sh', '-c',
        'cat %s | /usr/bin/gitosis-init' % pub_file],
      unless=[
        '/usr/bin/test', '-f', user_home+'/.gitosis.conf'],
      depends=[
        ref_resource('AptitudePackage', name='gitosis'),
        ref_resource('User', name=user_name)])
#test_gitosis('g2p-moulinex.pub')

gc = global_context()
gc.realize()

