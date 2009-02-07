# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import yaml

from systems.dsl import resource, transition
from systems.registry import Registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource


def is_valid_user(user):
  return user.wanted_attrs['present'] is True

class Rails(EResource):
  """
  A rails application.
  """

  def expand_into(self, rg):
    location = self.id_attrs['location']
    if not location.wanted_attrs['present']:
      raise ValueError

    rails_gem = rg.add_resource(resource('RubyGem',
      name='rails', version='2.1.2'))
    rake_pkg = rg.add_resource(resource('AptitudePackage',
      name='rake'))
    ruby_pgsql_pkg = rg.add_resource(resource('AptitudePackage',
      name='libpgsql-ruby'))
    ssl_pkg = rg.add_resource(resource('AptitudePackage',
      name='libopenssl-ruby1.8'))
    pkgs = rg.add_checkpoint(
        depends=(rails_gem, rake_pkg, ruby_pgsql_pkg, ssl_pkg))

    name = self.id_attrs['name']
    cluster_ref = rg.refs_received['cluster']
    run_user = self.wanted_attrs['run_user']
    run_user_name = run_user.id_attrs['name']
    run_user_ref = rg.refs_received['run_user']
    # XXX Need to give an ACL from db_maint_user to db_run_user.
    maint_user = self.wanted_attrs['maint_user']
    maint_user_name = maint_user.id_attrs['name']
    maint_user_ref = rg.refs_received['maint_user']

    # Same name means 'local ident sameuser' auth will work.
    db_run_user = rg.add_resource(resource('PgUser',
      name=run_user_name,
      cluster=cluster_ref,
      ))

    db_maint_user = rg.add_resource(resource('PgUser',
      name=maint_user_name,
      cluster=cluster_ref,
      ))

    db_conf_tree = {}
    migs = []
    for env in ('production', 'test', 'development', ):
      db_name = 'rails-%s-%s' % (name, env, )
      db_conf_tree[env] = {
          'adapter': 'postgresql',
          'database': db_name,
          'username': maint_user_name,
          }
      db = rg.add_resource(resource('PgDatabase',
        name=db_name,
        owner=db_maint_user,
        cluster=cluster_ref,
        ))
      # Testing for db:version retcode doesn't work anymore.
      mig = rg.add_transition(transition('Command',
        cmdline=['/usr/bin/rake', 'db:migrate'],
        username=maint_user_name,
        extra_env={ 'RAILS_ENV': env, },
        cwd=location.id_attrs['path'],
        ),
        depends=(
          maint_user_ref,
          rg.refs_received['location'],
          pkgs,
          db,
          ))
      migs.append(mig)

    db_conf_str = yaml.safe_dump(db_conf_tree, default_flow_style=False)
    db_conf_file = rg.add_resource(resource('PlainFile',
      path=location.id_attrs['path'] + '/config/database.yml',
      contents=db_conf_str,
      mode='0644',
      ),
      depends=(
        rg.refs_received['location'],
        ))
    for mig in migs:
      rg.add_dependency(db_conf_file, mig)


def register():
  # We should have UNIQUE (location) and UNIQUE (name),
  # not just a unique-together.
  restype = ResourceType('Rails', Rails,
    id_type={
      'name': AttrType(
        pytype=str),
      'location': RefAttrType(
        rtype='Directory'),
      },
    state_type={
      # More privileged
      'maint_user': RefAttrType(
        valid_condition=is_valid_user,
        rtype='User'),
      # Less privileged
      'run_user': RefAttrType(
        valid_condition=is_valid_user,
        rtype='User'),
      'cluster': RefAttrType(
        rtype='PgCluster'),
      })
  Registry.get_singleton().resource_types.register(restype)


