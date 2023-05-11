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
  'edit_item.py',
  'export_figure.py',
  'file_import.py',
  'file_io.py',
  'graphs.py',
  'item.py',
  'item_box.py',
  'main.py',
  'misc.py',
  'operations.py',
  'plot_settings.py',
  'plot_styles.py',
  'plotting_tools.py',
  'preferences.py',
  'rename.py',
  'transform_data.py',
  'ui.py',
  'utilities.py',
  'window.py',
]

python.install_sources(graphs_sources, subdir: project_name)
