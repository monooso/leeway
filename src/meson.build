pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'leeway'
gnome = import('gnome')

gnome.compile_resources('leeway',
  'ui/leeway.gresource.xml',
  source_dir: 'ui',
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
  'app/__init__.py',
  'app/api_client.py',
  'app/config.py',
  'app/credential_reader.py',
  'app/main.py',
  'app/preferences.py',
  'app/statusline.py',
  'app/usage_calculator.py',
  'app/usage_group.py',
  'app/usage_model.py',
  'app/window.py',
]

install_data(leeway_sources, install_dir: moduledir)
