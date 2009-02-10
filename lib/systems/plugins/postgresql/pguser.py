# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource

__all__ = ('register', )


def read_present(id_attrs):
  cluster = id_attrs['cluster'].unref
  name = id_attrs['name']
  return cluster.check_existence('pg_roles', 'rolname', name)

def create_user_trans(id_attrs):
  cluster = id_attrs['cluster'].unref
  name = id_attrs['name']
  return cluster.command_trans(
      cmdline=['/usr/bin/createuser', '-e',
        '-S', '-D', '-R', '-l', '-i',
        '--', name,
        ], )

def drop_user_trans(id_attrs):
  cluster = id_attrs['cluster'].unref
  name = id_attrs['name']
  return cluster.command_trans(
      cmdline=['/usr/bin/dropuser', '-e',
        '--', name,
        ], )

class PgUser(EResource):
  def expand_into(self, rg):
    cluster = self.id_attrs['cluster']
    p0, p1 = self.read_attrs()['present'], self.wanted_attrs['present']
    if (p0, p1) == (False, True):
      tr = rg.add_transition(create_user_trans(self.id_attrs), (cluster, ))
    elif (p0, p1) == (True, False):
      tr = rg.add_transition(drop_user_trans(self.id_attrs), (cluster, ))
    else:
      tr = None

    if tr is not None:
      if not cluster.wanted_attrs['present']:
        raise ValueError

def register():
  restype = ResourceType('PgUser', PgUser,
      id_type={
        'cluster': RefAttrType(
          rtype='PgCluster'),
        'name': AttrType(
          pytype=str),
        },
      state_type={
        'present': AttrType(
          default_value=True,
          pytype=bool,
          reader=read_present),
        })
  get_registry().resource_types.register(restype)


