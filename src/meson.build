# SPDX-License-Identifier: GPL-3.0-or-later
configure_file(
  input: 'graphs.in',
  output: meson.project_name(),
  configuration: conf,
  install: true,
  install_mode: 'rwxr-xr-x',
  install_dir: get_option('bindir')
)

graphs_sources = [
  'actions.py',
  'add_data_advanced.py',
  'add_equation.py',
  'canvas.py',
  'colorpicker.py',
  'data.py',
  'file_io.py',
  'graphs.py',
  'item_operations.py',
  'main.py',
  'misc.py',
  'operation.py',
  'plot_settings.py',
  'plotting_tools.py',
  'preferences.py',
  'rename_label.py',
  'samplerow.py',
  'transform_data.py',
  'ui.py',
  'utilities.py',
  'window.py',
]

install_data(graphs_sources, install_dir: moduledir, install_mode: 'rwxrwxrwx')
