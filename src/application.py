"""Adw.Application subclass for Headroom."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk

from config import APP_ID, VERSION
from window import ClaudeUsageWindow


class Application(Adw.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_startup(self):
        Adw.Application.do_startup(self)

        self.set_accels_for_action("window.close", ["<Control>w"])
        self.set_accels_for_action("app.quit", ["<Control>q"])

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)

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
        from preferences import PreferencesDialog

        dialog = PreferencesDialog()
        dialog.present(self.props.active_window)

    def _on_about(self, _action, _param):
        about = Adw.AboutDialog(
            application_name="Headroom",
            application_icon=APP_ID,
            version=VERSION,
            developer_name="Stephen Lewis",
            website="https://github.com/monooso/headroom",
            issue_url="https://github.com/monooso/headroom/issues",
            license_type=Gtk.License.AGPL_3_0,
        )
        about.present(self.props.active_window)
