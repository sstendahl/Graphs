pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'datman')
gnome = import('gnome')

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
  install_dir: get_option('bindir')
)

datman_sources = [
  '__init__.py',
  'samplerow.py',
  'datman.py',
  'plotting_tools.py',
  'toolbar.py',
  'item_operations.py',
  'colorpicker.py',
  'main.py',
  'window.py',
  'samplerow.py',
  'data.py',
  'window.ui',
  'sample_box.ui',
  'se.sjoerd.DatMan-symbolic.svg'
]

install_data(datman_sources, install_dir: moduledir)
