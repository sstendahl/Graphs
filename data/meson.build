# SPDX-License-Identifier: GPL-3.0-or-later
desktop_file_in = configure_file(
          input: application_id + '.desktop.in',
         output: application_id + '.desktop.in',
  configuration: conf,
)
desktop_file = i18n.merge_file(
        input: desktop_file_in,
       output: application_id + '.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(datadir, 'applications'),
)

desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
  test('Validate graphs desktop file', desktop_file_validate,
    args: [desktop_file.full_path()],
  )
endif

appstream_file_in = configure_file(
          input: application_id + '.appdata.xml.in',
         output: application_id + '.appdata.xml.in',
  configuration: conf,
)
appstream_file = i18n.merge_file(
        input: appstream_file_in,
       output: application_id + '.appdata.xml',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(datadir, 'appdata'),
)

# Validate Appdata
appstreamcli = find_program('appstreamcli', required: false)
if (appstreamcli.found())
  test('Validate appstream file', appstreamcli,
       args: ['validate', '--no-net', '--explain', appstream_file.full_path()],
    workdir: meson.current_build_dir(),
  )
endif

install_data(application_id + '.gschema.xml',
  install_dir: join_paths(datadir, 'glib-2.0/schemas'),
 install_mode: 'rwxrwxrwx',
)
gnome.compile_schemas(
  depend_files: [application_id + '.gschema.xml'],
)

install_data(application_id + '.mime.xml',
  install_dir: get_option('datadir') / 'mime/packages',
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()],
  )
endif

blueprint_files = [
  'ui/dialogs/delete-style.blp',
  'ui/dialogs/reset-import-settings.blp',
  'ui/dialogs/save-project-changes.blp',
  'ui/dialogs/save-style-changes.blp',
  'ui/add-equation.blp',
  'ui/add-style.blp',
  'ui/curve-fitting.blp',
  'ui/edit-item.blp',
  'ui/export-figure.blp',
  'ui/figure-settings-dialog.blp',
  'ui/figure-settings-page.blp',
  'ui/fitting-parameters.blp',
  'ui/import.blp',
  'ui/import-columns.blp',
  'ui/item-box.blp',
  'ui/shortcuts.blp',
  'ui/smoothen-settings.blp',
  'ui/style-color-box.blp',
  'ui/style-editor-box.blp',
  'ui/style-editor-window.blp',
  'ui/style-preview.blp',
  'ui/transform.blp',
  'ui/window.blp',
]

blueprints_ui = []
foreach b : blueprint_files
	blueprints_ui += b.replace('.blp', '.ui')
endforeach

blueprints = custom_target('blueprints',
    input: files(blueprint_files),
   output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

styles = files(
  'styles/adwaita.mplstyle',
  'styles/adwaita-dark.mplstyle',
  'styles/bmh.mplstyle',
  'styles/classic.mplstyle',
  'styles/dark-background.mplstyle',
  'styles/fivethirtyeight.mplstyle',
  'styles/ggplot.mplstyle',
  'styles/grayscale.mplstyle',
  'styles/matplotlib.mplstyle',
  'styles/seaborn.mplstyle',
  'styles/seaborn-bright.mplstyle',
  'styles/seaborn-colorblind.mplstyle',
  'styles/seaborn-dark-palette.mplstyle',
  'styles/seaborn-deep.mplstyle',
  'styles/seaborn-muted.mplstyle',
  'styles/seaborn-paper.mplstyle',
  'styles/seaborn-pastel.mplstyle',
  'styles/seaborn-poster.mplstyle',
  'styles/seaborn-talk.mplstyle',
  'styles/seaborn-ticks.mplstyle',
  'styles/seaborn-white.mplstyle',
  'styles/seaborn-whitegrid.mplstyle',
  'styles/solarized-light.mplstyle',
  'styles/tableau-colorblind10.mplstyle',
  'styles/thesis.mplstyle',
  'styles/yaru.mplstyle',
  'styles/yaru-dark.mplstyle',
)

icons = files (
  'icons/axes-one-quadrant-symbolic.svg',
  'icons/center-symbolic.svg',
  'icons/check-round-outline-whole-symbolic.svg',
  'icons/color-picker-symbolic.svg',
  'icons/derivative2-symbolic.svg',
  'icons/fast-fourier-transform-symbolic.svg',
  'icons/graph-symbolic.svg',
  'icons/function-third-order-symbolic.svg',
  'icons/history-undo-symbolic.svg',
  'icons/horizontal-arrows-symbolic.svg',
  'icons/info-symbolic.svg',
  'icons/image-print-symbolic.svg',
  'icons/integral-symbolic.svg',
  'icons/inverse-fast-fourier-transform-symbolic.svg',
  'icons/left-symbolic.svg',
  'icons/list-compact-symbolic.svg',
  'icons/loupe-symbolic.svg',
  'icons/move-tool-symbolic.svg',
  'icons/normalize-symbolic.svg',
  'icons/right-symbolic.svg',
  'icons/settings-symbolic.svg',
  'icons/shift-symbolic.svg',
  'icons/smoothen-symbolic.svg',
  'icons/transform-symbolic.svg',
  'icons/vertical-arrows-symbolic.svg',
  'icons/up-symbolic.svg',
  'icons/down-symbolic.svg',
)

other = files(
  'style.css',
  'style-hc.css',
  'whats_new',
)

gresource = custom_target('gresource',
    input: [blueprints, styles, icons, other],
   output: application_id + '.gresource.xml',
  depends: blueprints,
  command: [
    python,
    files('generate_gresource.py'),
    '@OUTPUT@',
    meson.current_build_dir(),
    files('../graphs/style_io.py'),
    '--styles', styles,
    '--ui', blueprints_ui,
    '--icons', icons,
    '--other', other,
  ],
)

gresource_hack = custom_target('gresource_hack',
    input: gresource,
   output: 'gresource_hack.vala',
  command: [find_program('touch'), '@OUTPUT@'],
)

gresource_bundle = gnome.compile_resources(application_id, gresource,
      dependencies: gresource,
  gresource_bundle: true,
        source_dir: meson.current_build_dir(),
           install: true,
       install_dir: pkgdatadir,
            c_name: meson.project_name(),
)

devenv.set('GRAPHS_OVERRIDE_RESOURCES', gresource_bundle.full_path())

scalable_dir = join_paths('icons', 'hicolor', 'scalable', 'apps')
icon_name = ('@0@.svg').format(application_id)
if debug
  icon_name = ('@0@.Devel.svg').format(application_id)
endif
install_data(join_paths(scalable_dir, icon_name),
       rename: ('@0@.svg').format(application_id),
  install_dir: join_paths(datadir, scalable_dir),
)

symbolic_dir = join_paths('icons', 'hicolor', 'symbolic', 'apps')
install_data(join_paths(symbolic_dir, ('@0@-symbolic.svg').format(application_id)),
  install_dir: join_paths(datadir, symbolic_dir),
)
