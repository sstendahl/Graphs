# SPDX-License-Identifier: GPL-3.0-or-later
python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', localedir)
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'graphs.in',
  output: 'graphs',
  configuration: conf,
  install: true,
  install_mode: 'rwxr-xr-x',
  install_dir: get_option('bindir')
)

graphs_sources = [
  'add_data_advanced.py',
  'add_equation.py',
  'canvas.py',
  'colorpicker.py',
  'data.py',
  'graphs.py',
  'item_operations.py',
  'main.py',
  'plot_settings.py',
  'plotting_tools.py',
  'preferences.py',
  'rename_label.py',
  'samplerow.py',
  'transform_data.py',
  'utilities.py',
  'window.py',
]

install_data(graphs_sources, install_dir: moduledir, install_mode: 'rwxrwxrwx')
