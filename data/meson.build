desktop_file = i18n.merge_file(
        input: application_id + '.desktop.in',
       output: application_id + '.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

appstream_file = i18n.merge_file(
        input: application_id + '.appdata.xml.in',
       output: application_id + '.appdata.xml',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util, args: ['validate', appstream_file])
endif

install_data(application_id + '.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas'),
    install_mode: 'rwxrwxrwx'
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file',
       compile_schemas,
       args: ['--strict', '--dry-run', meson.current_source_dir()])
endif

resources = gnome.compile_resources(
  application_id,
  application_id + '.gresource.xml',
  gresource_bundle: true,
  source_dir: meson.current_build_dir(),
  install: true,
  install_dir: pkgdatadir,
)

scalable_dir = join_paths('icons', 'hicolor', 'scalable', 'apps')
install_data(
  join_paths(scalable_dir, ('@0@.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir)
)

symbolic_dir = join_paths('icons', 'hicolor', 'symbolic', 'apps')
install_data(
  join_paths(symbolic_dir, ('@0@-symbolic.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', symbolic_dir)
)

icon_sources = [
  join_paths('icons', 'arrow1-left-symbolic.svg'),
  join_paths('icons', 'arrow1-right-symbolic.svg'),
  join_paths('icons', 'change-xscale-symbolic.svg'),
  join_paths('icons', 'change-yscale-symbolic.svg'),
  join_paths('icons', 'document-save-symbolic.svg'),
  join_paths('icons', 'go-home-symbolic.svg'),
  join_paths('icons', 'loupe-symbolic.svg'),
  join_paths('icons', 'move-tool-symbolic.svg'),
  join_paths('icons', 'pip-in-symbolic.svg'),
  join_paths('icons', 'settings-symbolic.svg'),
  join_paths('icons', 'arrow1-left-dark-symbolic.svg'),
  join_paths('icons', 'arrow1-right-dark-symbolic.svg'),
  join_paths('icons', 'change-xscale-dark-symbolic.svg'),
  join_paths('icons', 'change-yscale-dark-symbolic.svg'),
  join_paths('icons', 'document-save-dark-symbolic.svg'),
  join_paths('icons', 'go-home-dark-symbolic.svg'),
  join_paths('icons', 'loupe-dark-symbolic.svg'),
  join_paths('icons', 'move-tool-dark-symbolic.svg'),
  join_paths('icons', 'pip-in-dark-symbolic.svg'),
  join_paths('icons', 'settings-dark-symbolic.svg'),
]

install_data(icon_sources, install_dir: join_paths(moduledir, 'icons'), install_mode: 'rwxrwxrwx')
