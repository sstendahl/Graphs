# SPDX-License-Identifier: GPL-3.0-or-later
configure_file(
        input: 'graphs.in',
       output: project_name,
configuration: conf,
      install: true,
 install_mode: 'rwxr-xr-x',
  install_dir: bindir
)

python_sources = [
  'actions.py',
  'add_equation.py',
  'artist.py',
  'canvas.py',
  'clipboard.py',
  'data.py',
  'edit_item.py',
  'export_figure.py',
  'figure_settings.py',
  'file_import.py',
  'file_io.py',
  'item.py',
  'item_box.py',
  'main.py',
  'migrate.py',
  'misc.py',
  'operations.py',
  'preferences.py',
  'project.py',
  'scales.py',
  'styles.py',
  'transform_data.py',
  'ui.py',
  'utilities.py',
  'window.py',
]

python.install_sources(python_sources, subdir: project_name)

vala_sources = [
  'figure_settings.vala',
  'misc.vala',
]

graphs_lib = shared_library('graphs', vala_sources,
      vala_gir: 'Graphs-1.gir',
  dependencies: dependencies,
       install: true,
   install_dir: [true, true, true, true],
)

custom_target('graphs typelib',
       command: [find_program('g-ir-compiler'), '--shared-library', 'libgraphs.so', '--output', '@OUTPUT@', meson.current_build_dir() / 'Graphs-1.gir'],
        output: 'Graphs-1.typelib',
       depends: graphs_lib,
       install: true,
   install_dir: get_option('libdir') / 'girepository-1.0')