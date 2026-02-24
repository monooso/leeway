# preferences.py
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

"""Preferences dialog."""

from gi.repository import Adw, Gio, Gtk

from .config import APP_ID


@Gtk.Template(resource_path='/me/stephenlewis/Leeway/preferences-dialog.ui')
class LeewayPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = 'LeewayPreferencesDialog'

    interval_row = Gtk.Template.Child()
    notify_75_row = Gtk.Template.Child()
    notify_90_row = Gtk.Template.Child()
    notify_95_row = Gtk.Template.Child()
    test_notification_button = Gtk.Template.Child()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._settings = Gio.Settings.new(APP_ID)

        # Refresh interval: uint in GSettings, double in SpinRow
        self.interval_row.set_value(self._settings.get_uint('refresh-interval'))
        self.interval_row.connect(
            'notify::value',
            lambda row, _: self._settings.set_uint(
                'refresh-interval', int(row.get_value())
            ),
        )

        # Notification switches: boolean↔boolean, direct bind
        self._settings.bind(
            'notify-at-75', self.notify_75_row, 'active',
            Gio.SettingsBindFlags.DEFAULT,
        )
        self._settings.bind(
            'notify-at-90', self.notify_90_row, 'active',
            Gio.SettingsBindFlags.DEFAULT,
        )
        self._settings.bind(
            'notify-at-95', self.notify_95_row, 'active',
            Gio.SettingsBindFlags.DEFAULT,
        )

        # Test notification button
        self.test_notification_button.connect(
            'clicked', self._on_test_notification,
        )

    def _on_test_notification(self, _button):
        app = Gio.Application.get_default()
        if not app:
            self.add_toast(Adw.Toast(title='No running application instance'))
            return

        notification = Gio.Notification.new('Leeway: Test')
        notification.set_body('Notifications are working.')
        app.send_notification('test-notification', notification)
        self.add_toast(Adw.Toast(title='Test notification sent'))
