# main.py
#
# Copyright 2026 Stephen Lewis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import gi
import sys

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')

from gi.repository import Adw, Gio, Gtk
from .preferences import LeewayPreferencesDialog  # noqa: F401 — registers the GType
from .window import LeewayWindow

class LeewayApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='me.stephenlewis.Leeway',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/me/stephenlewis/Leeway')
        self.create_action('quit', lambda *_: self.quit(), ['<control>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<control>comma'])
        self.create_action('refresh', self.on_refresh_action, ['<control>r'])
        self.set_accels_for_action('window.close', ['<control>w'])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = LeewayWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='Leeway',
                                application_icon='me.stephenlewis.Leeway',
                                copyright='© 2026 Stephen Lewis',
                                developer_name='Stephen Lewis',
                                developers=['Stephen Lewis'],
                                issue_url='https://github.com/monooso/leeway/issues',
                                license_type=Gtk.License.AGPL_3_0,
                                version='1.0.0',
                                website='https://github.com/monooso/leeway')
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        dialog = LeewayPreferencesDialog()
        dialog.present(self.props.active_window)

    def on_refresh_action(self, widget, _):
        """Callback for the app.refresh action."""
        win = self.props.active_window
        if win:
            win.refresh()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application entry point."""
    app = LeewayApplication()
    return app.run(sys.argv)
