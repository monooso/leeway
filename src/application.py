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
            application_id="com.github.monooso.claude-usage-gnome",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_startup(self):
        Adw.Application.do_startup(self)

        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self._on_preferences)
        self.add_action(prefs_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ClaudeUsageWindow(application=self)
        win.present()

    def _on_preferences(self, _action, _param):
        from preferences import PreferencesWindow

        win = PreferencesWindow(transient_for=self.props.active_window)
        win.present()

    def _on_about(self, _action, _param):
        about = Adw.AboutDialog(
            application_name="Claude Usage",
            application_icon="com.github.monooso.claude-usage-gnome",
            version="0.1.0",
            developer_name="Stephen Lewis",
            website="https://github.com/monooso/claude-usage-gnome",
            issue_url="https://github.com/monooso/claude-usage-gnome/issues",
            license_type=Gtk.License.MIT_X11,
        )
        about.present(self.props.active_window)

# Need Gtk imported for License enum
from gi.repository import Gtk  # noqa: E402
