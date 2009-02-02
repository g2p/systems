# vim: set fileencoding=utf-8 sw=2 ts=2 et :

import re

from pguser import PgUser

from systems.dsl import resource
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource, Attrs
from systems.util.templates import build_and_render

__all__ = ('register', )

def read_present(id_attrs):
  cluster = id_attrs['user'].id_attrs['cluster']
  name = id_attrs['name']
  return cluster.check_existence('pg_database', 'datname', name)

def is_valid_dbname(name):
  # See the run-parts manpage for restrictions on cron file names.
  # We could encode stuff using dashes, but it's too much trouble.
  return re.match('^[a-z0-9-]*$', name)

def create_db_trans(id_attrs):
  user = id_attrs['user']
  cluster = user.id_attrs['cluster']
  name = id_attrs['name']
  username = user.id_attrs['name']
  return cluster.command_trans(
      cmdline=['/usr/bin/createdb', '-e',
        '--encoding', 'UTF8',
        '--owner', username,
        '--', name,
        ], )

def drop_db_trans(id_attrs):
  user = id_attrs['user']
  cluster = user.id_attrs['cluster']
  name = id_attrs['name']
  return cluster.command_trans(
      cmdline=['/usr/bin/dropdb', '-e',
        '--', name,
        ], )

class PgDatabase(Resource):
  def get_extra_deps(self):
    dbname = self.id_attrs['name']
    enable_backups = self.wanted_attrs['enable_backups']
    fname = '/etc/cron.daily/db-backup-' + dbname
    template = u'''#!/bin/sh
    set -e
    [ -e /usr/bin/pg_dump ] || exit 0
    exec /usr/bin/pg_dump -Fc \\
        -f /var/backups/postgresql/{{ dbname }}-$(/bin/date --rfc-3339=date) \\
        -- {{ dbname }}
    '''
    code = build_and_render(template, dbname=dbname)

    cron_file = resource('File',
        present=enable_backups,
        path=fname,
        mode=0700,
        contents=code.encode('utf8'), )

    user = self.id_attrs['user']

    return (user, cron_file)

  def place_transitions(self, transition_graph):
    # Caveat:
    # The db could be dropped between place_transitions and realization.
    p0, p1 = self.read_attrs()['present'], self.wanted_attrs['present']
    if (p0, p1) == (False, True):
      tg.add_transition(create_db_trans(self.id_attrs))
    elif (p0, p1) == (True, False):
      tg.add_transition(drop_db_trans(self.id_attrs))

def register():
  restype = ResourceType('PgDatabase', PgDatabase,
      id_type={
        'user': AttrType(
          pytype=PgUser),
        'name': AttrType(
          valid_condition=is_valid_dbname,
          pytype=str),
        },
      state_type={
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        'enable_backups': AttrType(
          default_value=True,
          pytype=bool),
        })
  Registry.get_singleton().resource_types.register(restype)


