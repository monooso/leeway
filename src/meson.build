pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'leeway'
gnome = import('gnome')

gnome.compile_resources('leeway',
  'leeway.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'leeway.in',
  output: 'leeway',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

leeway_sources = [
  '__init__.py',
  'api_client.py',
  'config.py',
  'credential_reader.py',
  'main.py',
  'preferences.py',
  'statusline.py',
  'usage_calculator.py',
  'usage_group.py',
  'usage_model.py',
  'window.py',
]

install_data(leeway_sources, install_dir: moduledir)
