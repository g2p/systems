# vim: set fileencoding=utf-8 sw=2 ts=2 et :
from __future__ import absolute_import

import jinja2
import re

# Boo globals.
_env = jinja2.Environment(undefined=jinja2.StrictUndefined)
_endline_re = re.compile(r'\r\n|\n|\r')

def jinja2_bug_workaround(s):
  # Work around this: http://dev.pocoo.org/projects/jinja/ticket/324
  if '\n'.join(s.splitlines()) != _endline_re.sub('\n', s):
    assert '\n'.join((s + '\n').splitlines()) == _endline_re.sub('\n', s)
    s += '\n'
  return s

def build_and_render(template_str, **kwargs):
  template_str = jinja2_bug_workaround(template_str)
  template = _env.from_string(template_str)
  return template.render(**kwargs)

