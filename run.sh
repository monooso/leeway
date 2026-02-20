#!/bin/bash
# Run Claude Usage directly without Meson build
# Requires: system Python 3 with PyGObject, GTK4, Libadwaita
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export GSETTINGS_SCHEMA_DIR="$SCRIPT_DIR/data"

# Compile the GSettings schema if needed
if [ ! -f "$GSETTINGS_SCHEMA_DIR/gschemas.compiled" ] || \
   [ "$GSETTINGS_SCHEMA_DIR/com.github.monooso.claude-usage-gnome.gschema.xml" -nt "$GSETTINGS_SCHEMA_DIR/gschemas.compiled" ]; then
    glib-compile-schemas "$GSETTINGS_SCHEMA_DIR"
fi

exec /usr/bin/python3 "$SCRIPT_DIR/src/main.py" "$@"
