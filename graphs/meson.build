# SPDX-License-Identifier: GPL-3.0-or-later
configure_file(
        input: 'graphs.in',
       output: project_name,
configuration: conf,
      install: true,
 install_mode: 'rwxr-xr-x',
  install_dir: bindir
)

python.install_sources(
  files(
    'actions.py',
    'add_equation.py',
    'application.py',
    'artist.py',
    'canvas.py',
    'curve_fitting.py',
    'data.py',
    'edit_item.py',
    'export_figure.py',
    'figure_settings.py',
    'file_import.py',
    'file_io.py',
    'item.py',
    'item_box.py',
    'migrate.py',
    'misc.py',
    'operations.py',
    'parse_file.py',
    'project.py',
    'scales.py',
    'style_io.py',
    'styles.py',
    'transform_data.py',
    'ui.py',
    'utilities.py',
  ),
  subdir: project_name
)

configure_file (output: 'config.h', configuration: vala_conf)
config_dep = valac.find_library ('config', dirs: meson.project_source_root () / 'graphs')
graphs_lib = shared_library(
  'graphs',
  files(
    'about.vala',
    'application.vala',
    'curve_fitting.vala',
    'data.vala',
    'figure_settings.vala',
    'interfaces.vala',
    'item.vala',
    'inline-stack-switcher.vala',
    'misc.vala',
    'smoothen_settings.vala',
    'styles.vala',
    'utilities.vala',
    'window.vala',
  ), blueprints_hack, gresource_bundle,
           vala_gir: 'Graphs-1.gir',
       dependencies: dependencies + config_dep,
include_directories: include_directories('.'),
         link_args : ['-lm',],
            install: true,
        install_dir: [true],
)

custom_target('graphs typelib',
       command: [find_program('g-ir-compiler'), '--shared-library', 'libgraphs.so', '--output', '@OUTPUT@', meson.current_build_dir() / 'Graphs-1.gir'],
        output: 'Graphs-1.typelib',
       depends: graphs_lib,
       install: true,
   install_dir: get_option('libdir') / 'girepository-1.0')
devenv.set('GI_TYPELIB_PATH', meson.current_build_dir())
