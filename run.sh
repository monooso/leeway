#!/bin/bash
# Run Headroom directly without Meson build
# Requires: system Python 3 with PyGObject, GTK4, Libadwaita
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export GSETTINGS_SCHEMA_DIR="$SCRIPT_DIR/data"

APP_ID="io.github.monooso.headroom"
VERSION=$(sed -n "s/.*version: *'\([^']*\)'.*/\1/p" "$SCRIPT_DIR/meson.build" | head -1)

# Compile the GSettings schema if needed
if [ ! -f "$GSETTINGS_SCHEMA_DIR/gschemas.compiled" ] || \
   [ "$GSETTINGS_SCHEMA_DIR/$APP_ID.gschema.xml" -nt "$GSETTINGS_SCHEMA_DIR/gschemas.compiled" ]; then
    glib-compile-schemas "$GSETTINGS_SCHEMA_DIR"
fi

# Generate config.py from template if needed
CONFIG="$SCRIPT_DIR/src/config.py"
TEMPLATE="$SCRIPT_DIR/src/config.py.in"
if [ ! -f "$CONFIG" ] || [ "$TEMPLATE" -nt "$CONFIG" ] || [ "$SCRIPT_DIR/meson.build" -nt "$CONFIG" ]; then
    sed -e "s|@VERSION@|$VERSION|g" -e "s|@APP_ID@|$APP_ID|g" "$TEMPLATE" > "$CONFIG"
fi

exec /usr/bin/python3 "$SCRIPT_DIR/src/main.py" "$@"
