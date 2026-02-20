python_path = get_option('python_path')

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

# Configure the launcher script with the correct python path and source dir
launcher_conf = configuration_data()
launcher_conf.set('PYTHON', python_path)
launcher_conf.set('SRCDIR', meson.current_source_dir())

configure_file(
  input: 'claude-usage.in',
  output: 'claude-usage',
  configuration: launcher_conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)
