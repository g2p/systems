# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import subprocess

from systems.dsl import resource, transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.transitions.file.directory import Directory


def is_valid_arg(st):
  # bool tests for emptiness
  return bool(st) and st[0] != '-'

def read_present(id_attrs):
  # Chicken and egg problem:
  # this won't work until we have installed rubygems.
  r = subprocess.call(['/usr/bin/gem',
    'query',
    '--quiet',
    '--installed',
    '--name-matches', id_attrs['name'],
    '--version', id_attrs['version'],
    ])
  if r == 0:
    return True
  elif r == 1:
    return False
  else:
    raise subprocess.CalledProcessError(r, '/usr/bin/gem')

class RubyGem(Resource):
  """
  A particular version of a ruby gem.
  """

  def expand_predepends_into(self, rg):
    # XXX Make context use this.
    gems = rg.add_resource(resource('AptitudePackage', 'rubygems'))

  def expand_into(self, rg):
    p0, p1 = self.read_attrs()['present'], self.wanted_attrs['present']
    if (p0, p1) == (False, True):
      tr = rg.add_transition(transition('Command',
        cmdline=['/usr/bin/gem', 'install',
          '--quiet',
          '--no-rdoc', '--no-ri',
          '--include-dependencies',
          '--version', self.id_attrs['version'],
          self.id_attrs['name'],
          ]))
    elif (p0, p1) == (True, False):
      tr = rg.add_transition(transition('Command',
        cmdline=['/usr/bin/gem', 'uninstall',
          '--quiet',
          self.id_attrs['name'],
          ]))


def register():
  restype = ResourceType('RubyGem', RubyGem,
    id_type={
      'name': AttrType(
        valid_condition=is_valid_arg,
        pytype=str),
      'version': AttrType(
        valid_condition=is_valid_arg,
        pytype=str),
      },
    state_type={
      'present': AttrType(
        default_value=True,
        reader=read_present,
        pytype=bool),
      })
  Registry.get_singleton().resource_types.register(restype)


