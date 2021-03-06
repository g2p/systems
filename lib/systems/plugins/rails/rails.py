# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import yaml

from systems.dsl import resource, transition
from systems.registry import get_registry
from systems.typesystem import AttrType, RefAttrType, ResourceType, EResource
from systems.util.templates import build_and_render


def is_valid_user(user):
  return user.wanted_attrs['present'] is True

class Rails(EResource):
  """
  A rails application.
  """

  def expand_into(self, rg):
    loc = self.id_attrs['location']
    loc_path = loc.id_attrs['path']
    if not loc.wanted_attrs['present']:
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
    hostname = self.wanted_attrs['hostname']
    cluster = self.wanted_attrs['cluster']
    run_user = self.wanted_attrs['run_user']
    run_user_name = run_user.id_attrs['name']
    # XXX Need to give an ACL from db_maint_user to db_run_user.
    maint_user = self.wanted_attrs['maint_user']
    maint_user_name = maint_user.id_attrs['name']

    # Same name means 'local ident sameuser' auth will work.
    db_run_user = rg.add_resource(resource('PgUser',
      name=run_user_name,
      cluster=cluster,
      ))

    db_maint_user = rg.add_resource(resource('PgUser',
      name=maint_user_name,
      cluster=cluster,
      ))

    sv_dir_loc = rg.add_resource(resource('Directory',
        path=loc_path+'/service',
        mode='0755',
        ),
      depends=(loc, ))

    sv_dir_serv_loc = rg.add_resource(resource('Directory',
        path='/etc/service/' + name,
        mode='0755',
        ))
    sv_dir_service = rg.add_resource(resource('DirService',
        location=sv_dir_serv_loc,
        target_dir=sv_dir_loc,
        ))

    db_conf_tree = {}
    migs = []
    # XXX Leads to conflicts
    env_ports = {'production': 4334, 'test': 5434, 'development': 6534, }
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
        cluster=cluster,
        ))
      # Testing for db:version retcode doesn't work anymore.
      mig = rg.add_transition(transition('Command',
        cmdline=['/usr/bin/rake', 'db:migrate'],
        username=maint_user_name,
        extra_env={ 'RAILS_ENV': env, },
        cwd=loc_path,
        ),
        depends=(maint_user, loc, pkgs, db, ))
      migs.append(mig)
      sv_loc_path = loc_path + '/service/' + env
      sv_loc = rg.add_resource(resource('Directory',
          path=sv_loc_path,
          mode='0755',
          ),
        depends=(sv_dir_loc, ))
      sv_contents = build_and_render('''#!/bin/sh
cd ../..
# Rails messages and backtraces are normally on stderr.
exec 2>&1
exec chpst -u {{ maint_user_name }} ./script/server webrick --environment {{ env }} --binding {{ binding_ip }} --port {{ port }}
''',
        maint_user_name=maint_user_name,
        env=env,
        binding_ip='127.0.0.1',
        port=env_ports[env],
        ).encode('utf8')
      sv = rg.add_resource(resource('Service',
          location=sv_loc,
          contents=sv_contents,
          status='down',
          ))
    tmp_dirs = rg.add_transition(transition('Command',
      cmdline=['/usr/bin/rake', 'tmp:create'],
      username=maint_user_name,
      cwd=loc_path,
      ),
      depends=(maint_user, loc, pkgs, ))

    db_conf_str = yaml.safe_dump(db_conf_tree, default_flow_style=False)
    db_conf_file = rg.add_resource(resource('PlainFile',
      path=loc_path + '/config/database.yml',
      contents=db_conf_str,
      mode='0644',
      ),
      depends=(loc, ))
    for mig in migs:
      rg.add_dependency(db_conf_file, mig)

    passenger_site = rg.add_resource(resource('PassengerSite',
        name=name,
        hostname=hostname,
        rails_dir=loc,
        ))


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
      'hostname': AttrType(
        default_value='localhost',
        pytype=str),
      'cluster': RefAttrType(
        rtype='PgCluster'),
      })
  get_registry().resource_types.register(restype)


