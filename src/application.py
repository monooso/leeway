"""Adw.Application subclass for Claude Usage."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib

from window import ClaudeUsageWindow


class Application(Adw.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id="com.github.sl.claude-usage",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ClaudeUsageWindow(application=self)
        win.present()
