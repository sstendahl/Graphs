# SPDX-License-Identifier: GPL-3.0-or-later
project('graphs',
          version: '1.6.1',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

application_id = 'se.sjoerd.Graphs'
name = 'Graphs'
copyright = '2022 - 2023'
homepage_url = 'https://graphs.sjoerd.se/'
github_url = 'https://github.com/sjoerd1993/Graphs'
issue_url = github_url + '/issues'
author = 'Sjoerd Stendahl'
description_short = 'Plot and manipulate data in a breeze'

i18n = import('i18n')
gnome = import('gnome')
python = import('python').find_installation('python3')

prefix = get_option('prefix')
datadir = get_option('datadir')
bindir = get_option('bindir')
version = meson.project_version()
project_name = meson.project_name()
pkgdatadir = join_paths(prefix, datadir, meson.project_name())
localedir = join_paths(prefix, get_option('localedir'))
debug = get_option('buildtype') == 'debug'

if debug
  version += '-' + run_command('git', 'rev-parse', '--short', 'HEAD', check: true).stdout().strip()
  name += ' (Development)'
endif

conf = configuration_data()
conf.set('APPLICATION_ID', application_id)
conf.set('AUTHOR', author)
conf.set('COPYRIGHT', copyright)
conf.set('DESCRIPTION_SHORT', description_short)
conf.set('GITHUB_URL', github_url)
conf.set('ISSUE_URL', issue_url)
conf.set('LOCALEDIR', localedir)
conf.set('NAME', name)
conf.set('PKGDATADIR', pkgdatadir)
conf.set('PROJECT_NAME', project_name)
conf.set('PYTHON', python.full_path())
conf.set('VERSION', version)
conf.set('HOMEPAGE_URL', homepage_url)

if debug
  conf.set('LOG_LEVEL', 'DEBUG')
else
  conf.set('LOG_LEVEL', 'INFO')
endif

subdir('data')
subdir('src')
subdir('po')

test_env = [
    'pkgdatadir={pkgdatadir}',
    'application_id='.format(application_id),
]

test(
    'pytest',
    find_program('pytest'),
    args: [meson.project_source_root() + '/tests'],
    env: [
        'pkgdatadir=' + pkgdatadir,
        'application_id=' + application_id,
    ],
)


gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
