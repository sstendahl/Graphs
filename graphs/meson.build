# SPDX-License-Identifier: GPL-3.0-or-later
configure_file(
          input: 'graphs.in',
         output: meson.project_name(),
  configuration: conf,
        install: true,
   install_mode: 'rwxr-xr-x',
    install_dir: bindir,
)

python.install_sources(
  files(
    'application.py',
    'artist.py',
    'canvas.py',
    'curve_fitting.py',
    'data.py',
    'edit_item.py',
    'export_items.py',
    'file_import.py',
    'file_io.py',
    'item.py',
    'migrate.py',
    'misc.py',
    'operations.py',
    'parse_file.py',
    'project.py',
    'python_helper.py',
    'scales.py',
    'style_editor.py',
    'style_io.py',
    'styles.py',
    'utilities.py',
    'window.py',
  ),
  subdir: meson.project_name(),
)

configure_file(
         output: 'config.h',
  configuration: vala_conf
)
config_dep = valac.find_library('config',
  dirs: meson.project_source_root () / 'graphs'
)
graphs_lib = shared_library('graphs',
  files(
    'actions.vala',
    'add_equation.vala',
    'application.vala',
    'canvas.vala',
    'curve_fitting.vala',
    'data.vala',
    'export_figure.vala',
    'export_items.vala',
    'figure_settings.vala',
    'file_import.vala',
    'item.vala',
    'inline-stack-switcher.vala',
    'item_box.vala',
    'misc.vala',
    'project.vala',
    'python_helper.vala',
    'smoothen_settings.vala',
    'style_editor.vala',
    'styles.vala',
    'transform.vala',
    'utilities.vala',
    'window.vala',
  ), gresource_bundle,
             vala_gir: 'Graphs-1.gir',
         dependencies: dependencies + config_dep,
  include_directories: include_directories('.'),
            link_args: ['-lm',],
              install: true,
          install_dir: [true],
)

custom_target('graphs typelib',
      command: [find_program('g-ir-compiler'), '--shared-library', 'libgraphs.so', '--output', '@OUTPUT@', meson.current_build_dir() / 'Graphs-1.gir'],
       output: 'Graphs-1.typelib',
      depends: graphs_lib,
      install: true,
  install_dir: get_option('libdir') / 'girepository-1.0',
 )
devenv.set('GI_TYPELIB_PATH', meson.current_build_dir())
