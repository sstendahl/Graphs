pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'datman')
gnome = import('gnome')

subdir('icons')

gnome.compile_resources('datman',
  'datman.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'datman.in',
  output: 'datman',
  configuration: conf,
  install: true,
  install_mode: 'rwxr-xr-x',
  install_dir: get_option('bindir')
)

datman_sources = [
  '__init__.py',
  'add_data_advanced.py',
  'add_equation.py',
  'colorpicker.py',
  'config.json',
  'data.py',
  'datman.in',
  'datman.py',
  'item_operations.py',
  'main.py',
  'pip_mode.py',
  'plot_settings.py',
  'plotting_tools.py',
  'preferences.py',
  'rename_label.py',
  'samplerow.py',
  'toolbar.py',
  'transform_data.py',
  'utilities.py',
  'window.py',
]

install_data(datman_sources, install_dir: moduledir, install_mode: 'rwxrwxrwx')
