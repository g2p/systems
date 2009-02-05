# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

from systems.dsl import resource
from systems.registry import Registry
from systems.typesystem import AttrType, ResourceType, Resource
from systems.transitions.file.directory import Directory


class Redmine(Resource):
  """
  A redmine instance.
  """

  def expand_into(self, rg):
    svn_branch = self.wanted_attrs['svn_branch']
    rails_name = 'redmine-%s' % self.id_attrs['name']
    # Privileged (create tables, update checkout)
    maint_user_name = 'redmine-maint-%s' % self.id_attrs['name']
    # Less privileged (run server, write temporary files)
    run_user_name = 'redmine-run-%s' % self.id_attrs['name']

    run_user = resource('User', name=run_user_name)
    maint_user = rg.add_resource(resource('User', name=maint_user_name))
    loc = rg.add_resource(resource('Directory',
        path=self.id_attrs['path'],
        owner=maint_user_name,
        mode='0755',
        ),
      maint_user)
    co = rg.add_resource(resource('SvnWorkingCopy',
        location=loc,
        url=svn_branch,
        ))
    pub_assets = rg.add_resource(resource('Directory',
        path=loc.id_attrs['path'] + '/public/plugin_assets',
        owner=maint_user_name,
        ),
      co)
    loc_ref = loc.make_reference()
    loc_ref = rg.add_reference(loc_ref, pub_assets)

    rails = rg.add_resource(resource('Rails',
        name=rails_name,
        location=loc_ref,
        maint_user=maint_user,
        run_user=run_user,
        ))


def register():
  restype = ResourceType('Redmine', Redmine,
    id_type={
      # They must be _separately_ unique.
      'path': AttrType(
        pytype=str),
      'name': AttrType(
        pytype=str),
      },
    state_type={
      'svn_branch': AttrType(
        default_value='http://redmine.rubyforge.org/svn/branches/0.8-stable/',
        pytype=str),
      })
  Registry.get_singleton().resource_types.register(restype)


