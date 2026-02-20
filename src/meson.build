python_path = get_option('python_path')
pkgdatadir = get_option('prefix') / get_option('datadir') / 'claude-usage-gnome'

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

# Configure the launcher script with the correct python path and installed source dir
launcher_conf = configuration_data()
launcher_conf.set('PYTHON', python_path)
launcher_conf.set('PKGDATADIR', pkgdatadir)

configure_file(
  input: 'claude-usage-gnome.in',
  output: 'claude-usage-gnome',
  configuration: launcher_conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)
