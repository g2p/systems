# vim: set fileencoding=utf-8 sw=2 ts=2 et :

import re

from pgdatabase import PgDatabase

from systems.dsl import resource
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource, Attrs
from systems.util.templates import build_and_render

__all__ = ('register', )

def is_valid_db(db):
  name = db.id_attrs['name']
  # See the run-parts manpage for restrictions on cron file names.
  # We could encode stuff using dashes, but it's too much trouble.
  return re.match('^[a-z0-9-]*$', name)

def is_valid_state(state):
  return state in ('present', 'absent', )

class PgDbBackup(Resource):
  def place_extra_deps(self, resource_graph):
    resource_graph.add_dependency(self.id_attrs['database'], self)

  def place_transitions(self, transition_graph):
    dbname = self.id_attrs['database'].id_attrs['name']
    state = self.wanted_attrs['state']

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
        state=state,
        path=fname,
        mode=0700,
        contents=code.encode('utf8'), )
    return cron_file.place_transitions(transition_graph)

def register():
  restype = ResourceType('PgDbBackup', PgDbBackup,
      id_type={
        'database': AttrType(
      pytype=PgDatabase,
      valid_condition=is_valid_db),
        },
      state_type={
        'state': AttrType(
      default_value='present',
      valid_condition=is_valid_state),
  })
  Registry.get_singleton().resource_types.register(restype)


