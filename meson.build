# SPDX-License-Identifier: GPL-3.0-or-later
project('graphs',
          version: '1.4.1',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

application_id = 'se.sjoerd.Graphs'
name = 'Graphs'
copyright = '2022 - 2023'
website = 'https://www.sjoerd.se/Graphs'
github = 'https://github.com/SjoerdB93/Graphs'
issues = 'https://github.com/SjoerdB93/Graphs/issues'
author = 'Sjoerd Broekhuijsen'
description_short = 'Plot and manipulate data in a breeze'

i18n = import('i18n')
gnome = import('gnome')
fs = import('fs')
python = import('python')

prefix = get_option('prefix')
datadir = get_option('datadir')
bindir = get_option('bindir')
version = meson.project_version()
project_name = meson.project_name()
pkgdatadir = join_paths(prefix, datadir, meson.project_name())
moduledir = join_paths(pkgdatadir, meson.project_name())
localedir = join_paths(prefix, get_option('localedir'))
debug = get_option('buildtype') == 'debug'

if debug
  version += '-' + run_command('git', 'rev-parse', '--short', 'HEAD', check: true).stdout().strip()
  name += ' (Development)'
  application_id += '.Devel'
endif

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('project', project_name)
conf.set('version', version)
conf.set('localedir', localedir)
conf.set('pkgdatadir', pkgdatadir)
conf.set('copyright', copyright)
conf.set('appid', application_id)
conf.set('name', name)
conf.set('website', website)
conf.set('github', github)
conf.set('issues', issues)
conf.set('author', author)
conf.set('description_short', description_short)
if debug
  conf.set('log_level', 'DEBUG')
else
  conf.set('log_level', 'INFO')
endif

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
