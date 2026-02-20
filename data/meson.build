desktop_conf = configuration_data()
desktop_conf.set('APP_ID', app_id)
desktop_conf.set('BINDIR', bindir)

desktop_file = configure_file(
  input: 'io.github.monooso.claude-usage-gnome.desktop.in',
  output: '@BASENAME@',
  configuration: desktop_conf,
  install: true,
  install_dir: datadir / 'applications',
)

install_data(
  'io.github.monooso.claude-usage-gnome.gschema.xml',
  install_dir: datadir / 'glib-2.0' / 'schemas',
)

gnome.compile_schemas(depend_files: files('io.github.monooso.claude-usage-gnome.gschema.xml'))

metainfo_conf = configuration_data()
metainfo_conf.set('APP_ID', app_id)

configure_file(
  input: 'io.github.monooso.claude-usage-gnome.metainfo.xml.in',
  output: '@BASENAME@',
  configuration: metainfo_conf,
  install: true,
  install_dir: datadir / 'metainfo',
)

install_subdir(
  'icons',
  install_dir: datadir,
)
