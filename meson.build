project('claude-usage',
  version: '0.1.0',
  meson_version: '>= 0.62.0',
  default_options: ['warning_level=2'],
)

python = import('python')
py_installation = python.find_installation('python3')
gnome = import('gnome')

dependency('gtk4', version: '>= 4.10')
dependency('libadwaita-1', version: '>= 1.4')
dependency('libsoup-3.0', version: '>= 3.0')

app_id = 'com.github.monooso.claude-usage-gnome'
prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')

subdir('data')
subdir('src')
