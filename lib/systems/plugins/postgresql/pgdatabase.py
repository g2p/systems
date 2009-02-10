# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import re

from systems.dsl import resource
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource
from systems.util.templates import build_and_render

__all__ = ('register', )

def read_present(id_attrs):
  cluster = id_attrs['cluster'].unref
  name = id_attrs['name']
  return cluster.check_existence('pg_database', 'datname', name)

def is_valid_dbname(name):
  # See the run-parts manpage for restrictions on cron file names.
  # We could encode stuff using dashes, but it's too much trouble.
  return re.match('^[a-z0-9-]*$', name)

class PgDatabase(EResource):
  def expand_into(self, rg):
    owner = self.wanted_attrs['owner']
    cluster = self.id_attrs['cluster']
    if owner.id_attrs['cluster'].unref != cluster:
      raise ValueError

    p0, p1 = self.read_attrs()['present'], self.wanted_attrs['present']
    if (p0, p1) == (False, True):
      tr = rg.add_transition(self.create_db_trans(), (owner, cluster))
    elif (p0, p1) == (True, True):
      tr = rg.add_transition(self.update_owner_trans(), (owner, cluster))
    elif (p0, p1) == (True, False):
      tr = rg.add_transition(self.drop_db_trans(), (owner, cluster))

    enable_backups = p1 and self.wanted_attrs['enable_backups']
    rg.add_resource(self.cron_backup_res(enable_backups))

  def cron_backup_res(self, enable_backups):
    dbname = self.id_attrs['name']
    template = u'''#!/bin/sh
set -e
[ -e /usr/bin/pg_dump ] || exit 0
exec /usr/bin/pg_dump -Fc \\
    -f /var/backups/postgresql/{{ dbname }}-$(/bin/date --rfc-3339=date) \\
    -- {{ dbname }}
'''
    code = build_and_render(template, dbname=dbname)

    fname = '/etc/cron.daily/db-backup-' + dbname
    return resource('PlainFile',
        present=enable_backups,
        path=fname,
        mode='0700',
        contents=code.encode('utf8'), )

  def create_db_trans(self):
    ownername = self.wanted_attrs['owner'].id_attrs['name']
    cluster = self.id_attrs['cluster'].unref
    name = self.id_attrs['name']
    return cluster.command_trans(
        cmdline=['/usr/bin/createdb', '-e',
          '--encoding', 'UTF8',
          '--owner', ownername,
          '--', name,
          ], )

  def update_owner_trans(self):
    ownername = self.wanted_attrs['owner'].id_attrs['name']
    name = self.id_attrs['name']
    sql = build_and_render(
        """ALTER DATABASE "{{ name }}" OWNER TO "{{ ownername }}";""",
        name=name, ownername=ownername)
    sql = sql.encode('utf8')

    cluster = self.id_attrs['cluster'].unref
    return cluster.psql_eval_trans(sql)

  def drop_db_trans(self):
    cluster = self.id_attrs['cluster'].unref
    name = self.id_attrs['name']
    return cluster.command_trans(
        cmdline=['/usr/bin/dropdb', '-e',
          '--', name,
          ], )

def register():
  restype = ResourceType('PgDatabase', PgDatabase,
      id_type={
        'cluster': RefAttrType(
          rtype='PgCluster'),
        'name': AttrType(
          valid_condition=is_valid_dbname,
          pytype=str),
        },
      state_type={
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        'owner': RefAttrType(
          rtype='PgUser'),
        'enable_backups': AttrType(
          default_value=True,
          pytype=bool),
        })
  get_registry().resource_types.register(restype)


