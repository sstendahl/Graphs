# SPDX-License-Identifier: GPL-3.0-or-later
configure_file(
  input: 'graphs.in',
  output: project_name,
  configuration: conf,
  install: true,
  install_mode: 'rwxr-xr-x',
  install_dir: bindir
)

graphs_sources = [
  'actions.py',
  'add_data_advanced.py',
  'add_equation.py',
  'calculation.py',
  'clipboard.py',
  'canvas.py',
  'colorpicker.py',
  'data.py',
  'edit_item.py',
  'file_io.py',
  'graphs.py',
  'main.py',
  'misc.py',
  'operations.py',
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
