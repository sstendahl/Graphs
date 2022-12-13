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
  install_mode: 'rwxr-xr-x',
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
  'config.json',
  'samplerow.py',
  'transform_data.py',
  'data.py',
  'preferences.py',
  'forwards-symbolic.svg',
  'forwards-dark-symbolic.svg',
  'backwards-symbolic.svg',
  'backwards-dark-symbolic.svg',
  'zoom-symbolic.svg',
  'zoom-dark-symbolic.svg',
  'save-symbolic.svg',
  'save-dark-symbolic.svg',
  'move-symbolic.svg',
  'move-dark-symbolic.svg',
  'home-symbolic.svg',
  'home-dark-symbolic.svg',
  'change-xscale-symbolic.svg',
  'change-yscale-symbolic.svg',
  'change-xscale-dark-symbolic.svg',
  'change-yscale-dark-symbolic.svg',
  'datman.in',
]

install_data(datman_sources, install_dir: moduledir, install_mode: 'rwxrwxrwx')
