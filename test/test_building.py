import jinja2

import systems.context
import systems.resources
from systems.resource import ensure_resource, ref_resource

systems.resources.register()

ensure_resource('User',
    name='zorglub', state='absent')

ensure_resource('Command',
    name='foo', cmdline=['/bin/echo', '434'])

env = jinja2.Environment(undefined=jinja2.StrictUndefined)
template = env.from_string('Hello {{ name }}!\n')

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

gc = systems.context.global_context()
gc.realize()

