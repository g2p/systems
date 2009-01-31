# vim: set fileencoding=utf-8 sw=2 ts=2 et :

import re

from pgdatabase import PgDatabase

from systems.registry import Registry
from systems.realizable import Transition
from systems.realizable_dsl import transition
from systems.typesystem import Type, AttrType
from systems.util.templates import build_and_render

__all__ = ('register', )

def is_valid_db(db):
  name = db.attributes['name']
  # See the run-parts manpage for restrictions on cron file names.
  # We could encode stuff using dashes, but it's too much trouble.
  return re.match('^[a-z0-9-]*$', name)

def is_valid_state(state):
  return state in ('present', 'absent', )

class PgDbBackup(Transition):
  def realize(self):
    dbname = self.attributes['database'].attributes['name']
    state = self.attributes['state']

    fname = '/etc/cron.daily/db-backup-' + dbname
    template = u'''#!/bin/sh
    set -e
    [ -e /usr/bin/pg_dump ] || exit 0
    exec /usr/bin/pg_dump -Fc \\
        -f /var/backups/postgresql/{{ dbname }}-$(/bin/date --rfc-3339=date) \\
        -- {{ dbname }}
    '''
    code = build_and_render(template, dbname=dbname)

    cron_trans = transition('File',
        state=state,
        path=fname,
        mode=0700,
        contents=code.encode('utf8'), )
    cron_trans.realize()

def register():
  restype = Type('PgDbBackup', PgDbBackup,
    [
    # XXX We need to auto-create a dependency to this attribute
    AttrType('database',
      identifying=True,
      pytype=PgDatabase,
      valid_condition=is_valid_db),
    AttrType('state',
      default_value='present',
      valid_condition=is_valid_state),
  ])
  Registry.get_singleton().transition_types.register(restype)


