python_path = get_option('python_path')
pkgdatadir = get_option('prefix') / get_option('datadir') / 'headroom'

sources = files(
  'main.py',
  'application.py',
  'window.py',
  'credential_reader.py',
  'api_client.py',
  'usage_model.py',
  'usage_calculator.py',
  'preferences.py',
  'statusline.py',
)

install_data(sources, install_dir: pkgdatadir)

# Generate config.py with build-time values
config_data = configuration_data()
config_data.set('VERSION', meson.project_version())
config_data.set('APP_ID', app_id)

configure_file(
  input: 'config.py.in',
  output: 'config.py',
  configuration: config_data,
  install: true,
  install_dir: pkgdatadir,
)

# Configure the launcher script with the correct python path and installed source dir
launcher_conf = configuration_data()
launcher_conf.set('PYTHON', python_path)
launcher_conf.set('PKGDATADIR', pkgdatadir)

configure_file(
  input: 'headroom.in',
  output: 'headroom',
  configuration: launcher_conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)
