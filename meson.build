project('graphs',
          version: '1.4.0',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

application_id = 'se.sjoerd.Graphs'

i18n = import('i18n')
gnome = import('gnome')

datadir = get_option('datadir')
pkgdatadir = join_paths(get_option('prefix'), datadir, meson.project_name())
moduledir = join_paths(pkgdatadir, meson.project_name())

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
