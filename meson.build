# SPDX-License-Identifier: GPL-3.0-or-later
project('graphs',
          version: '1.4.1',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

application_id = 'se.sjoerd.Graphs'

i18n = import('i18n')
gnome = import('gnome')

prefix = get_option('prefix')
datadir = get_option('datadir')
pkgdatadir = join_paths(prefix, datadir, meson.project_name())
moduledir = join_paths(pkgdatadir, meson.project_name())
localedir = join_paths(prefix, get_option('localedir'))

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
