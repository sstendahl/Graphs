# SPDX-License-Identifier: GPL-3.0-or-later
desktop_file_in = configure_file(
        input: application_id + '.desktop.in.in',
       output: application_id + '.desktop.in',
configuration: conf
)

desktop_file = i18n.merge_file(
        input: desktop_file_in,
       output: application_id + '.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(datadir, 'applications')
)

desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
  test(
    'Validate desktop file',
    desktop_file_validate,
    args: [
      desktop_file.full_path()
    ]
  )
endif

appstream_file_in = configure_file(
        input: application_id + '.appdata.xml.in.in',
       output: application_id + '.appdata.xml.in',
configuration: conf
)

appstream_file = i18n.merge_file(
        input: appstream_file_in,
       output: application_id + '.appdata.xml',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(datadir, 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test(
    'Validate appstream file', appstream_util,
    args: ['validate', '--nonet', appstream_file.full_path()]
  )
endif

install_data(application_id + '.gschema.xml',
  install_dir: join_paths(datadir, 'glib-2.0/schemas'),
 install_mode: 'rwxrwxrwx'
)


install_data(
  application_id + '.mime.xml',
  install_dir: get_option('datadir') / 'mime/packages',
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file',
       compile_schemas,
       args: ['--strict', '--dry-run', meson.current_source_dir()])
endif

blueprints_source = [
  'ui/add_equation_window.blp',
  'ui/add_style.blp',
  'ui/curve_fitting.blp',
  'ui/dialogs.blp',
  'ui/edit_item.blp',
  'ui/export_figure.blp',
  'ui/figure_settings.blp',
  'ui/fitting_parameters.blp',
  'ui/import.blp',
  'ui/help_overlay.blp',
  'ui/item_box.blp',
  'ui/smoothen_settings.blp',
  'ui/style_color_box.blp',
  'ui/style_editor.blp',
  'ui/style_preview.blp',
  'ui/transform_window.blp',
  'ui/window.blp'
]

blueprints_ui = []
blueprints_vala = []
foreach b : blueprints_source
  blueprints_ui += b.replace('.blp', '.ui')
  blueprints_vala += b.replace('ui/', '') + '.vala'
endforeach

blueprints = custom_target('blueprints',
  input: blueprints_source,
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

blueprints_hack = custom_target('blueprints_hack',
  input: blueprints,
  output: blueprints_vala,
  command: [find_program('touch'), '@OUTPUT@'],
)

styles = [
  'adwaita',
  'adwaita-dark',
  'bmh',
  'classic',
  'dark-background',
  'fivethirtyeight',
  'ggplot',
  'grayscale',
  'seaborn',
  'seaborn-bright',
  'seaborn-colorblind',
  'seaborn-dark',
  'seaborn-darkgrid',
  'seaborn-dark-palette',
  'seaborn-deep',
  'seaborn-muted',
  'seaborn-notebook',
  'seaborn-paper',
  'seaborn-pastel',
  'seaborn-poster',
  'seaborn-talk',
  'seaborn-ticks',
  'seaborn-white',
  'seaborn-whitegrid',
  'solarized-light',
  'tableau-colorblind10',
  'thesis',
  'yaru',
  'yaru-dark'
]

gresource_conf = configuration_data()
style_conf = ''
preview_conf = ''
foreach style : styles
  style_conf += '    <file compressed="True">styles/' + style + '.mplstyle</file>\n'
  preview_conf += '    <file compressed="True">previews/' + style + '.svg</file>\n'
endforeach
gresource_conf.set('STYLES', style_conf)
gresource_conf.set('PREVIEWS', preview_conf)
ui_conf = ''
foreach b : blueprints_ui
  ui_conf += '    <file preprocess="xml-stripblanks">' + b + '</file>\n'
endforeach
gresource_conf.set('UI', ui_conf)

gresource_name = application_id + '.gresource.xml'
gresource = configure_file(
        input: gresource_name + '.in',
       output: gresource_name,
configuration: gresource_conf
)

gresource_bundle = gnome.compile_resources(
  application_id, gresource,
    dependencies: gresource,
gresource_bundle: true,
      source_dir: meson.current_build_dir(),
         install: true,
     install_dir: pkgdatadir,
          c_name: project_name,
)

scalable_dir = join_paths('icons', 'hicolor', 'scalable', 'apps')
icon_name = ('@0@.svg').format(application_id)
if debug
  icon_name = ('@0@.Devel.svg').format(application_id)
endif
install_data(
  join_paths(scalable_dir, icon_name),
     rename: ('@0@.svg').format(application_id),
install_dir: join_paths(datadir, scalable_dir)
)

symbolic_dir = join_paths('icons', 'hicolor', 'symbolic', 'apps')
install_data(
  join_paths(symbolic_dir, ('@0@-symbolic.svg').format(application_id)),
  install_dir: join_paths(datadir, symbolic_dir)
)
