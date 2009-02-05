# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import yaml

from systems.dsl import resource, transition
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.transitions.file.directory import Directory
from systems.transitions.user import User


def is_valid_user(user):
  return user.wanted_attrs['present'] is True

def get_user(user, default_name, rg):
  if user is None:
    # See about avoiding creating those users a home:
    # --no-create-home, now to find the correct resource attrs.
    user = resource('User', name=default_name, )
    user_name = default_name
  else:
    user_name = user.id_attrs['name']
  user = rg.add_resource(user)
  return user, user_name

class Rails(Resource):
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
    pkgs = rg.add_checkpoint(rails_gem, rake_pkg, ruby_pgsql_pkg, ssl_pkg)

    name = self.id_attrs['name']
    run_user, run_user_name = get_user(
        self.wanted_attrs['run_user'], 'rails-run-%s' % name, rg)
    maint_user, maint_user_name = get_user(
        self.wanted_attrs['maint_user'], 'rails-maint-%s' % name, rg)
    # Same name means 'local ident sameuser' auth will work.
    # Problem: how can I give a different user for migrations
    # and normal connections, in database.yml ?
    db_user = rg.add_resource(resource('PgUser', name=run_user_name, ))
    location = rg.add_resource(location)

    db_conf_tree = {}
    migs = []
    for env in ('production', 'test', 'development', ):
      db_name = 'rails-%s-%s' % (name, env, )
      db_conf_tree[env] = {
          'adapter': 'postgresql',
          'database': db_name,
          'username': run_user_name,
          }
      db = rg.add_resource(resource('PgDatabase',
        name=db_name,
        owner=db_user,
        ))
      # Testing for db:version retcode doesn't work anymore.
      mig = rg.add_transition(transition('Command',
        cmdline=['/usr/bin/rake', 'db:migrate'],
        username=run_user.id_attrs['name'],
        extra_env={ 'RAILS_ENV': env, },
        cwd=location.id_attrs['path'],
        ), run_user, db, pkgs, location)
      migs.append(mig)

    db_conf_str = yaml.safe_dump(db_conf_tree, default_flow_style=False)
    db_conf_file = rg.add_resource(resource('PlainFile',
      path=location.id_attrs['path'] + '/config/database.yml',
      contents=db_conf_str,
      mode='0644',
      ), location)
    for mig in migs:
      rg.add_dependency(db_conf_file, mig)


def register():
  # We should have UNIQUE (location) and UNIQUE (name),
  # not just a unique-together.
  restype = ResourceType('Rails', Rails,
    id_type={
      'name': AttrType(
        pytype=str),
      'location': AttrType(
        rtype='Directory'),
      },
    state_type={
      # More privileged
      'maint_user': AttrType(
        valid_condition=is_valid_user,
        none_allowed=True,
        rtype='User'),
      # Less privileged
      'run_user': AttrType(
        valid_condition=is_valid_user,
        none_allowed=True,
        rtype='User'),
      })
  Registry.get_singleton().resource_types.register(restype)


