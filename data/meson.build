desktop_conf = configuration_data()
desktop_conf.set('APP_ID', app_id)
desktop_conf.set('BINDIR', bindir)

desktop_file = configure_file(
  input: 'com.github.sl.claude-usage.desktop.in',
  output: '@BASENAME@',
  configuration: desktop_conf,
  install: true,
  install_dir: datadir / 'applications',
)

install_data(
  'com.github.sl.claude-usage.gschema.xml',
  install_dir: datadir / 'glib-2.0' / 'schemas',
)

gnome.compile_schemas(depend_files: files('com.github.sl.claude-usage.gschema.xml'))

metainfo_conf = configuration_data()
metainfo_conf.set('APP_ID', app_id)

configure_file(
  input: 'com.github.sl.claude-usage.metainfo.xml.in',
  output: '@BASENAME@',
  configuration: metainfo_conf,
  install: true,
  install_dir: datadir / 'metainfo',
)

install_subdir(
  'icons',
  install_dir: datadir,
)
