"""Preferences dialog."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from config import APP_ID
from statusline import (
    BrokenSymlinkError,
    CorruptSettingsError,
    DEFAULT_SCRIPT_PATH,
    install_statusline,
    uninstall_statusline,
)


class PreferencesDialog(Adw.PreferencesDialog):
    """Application preferences."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Preferences")
        self.set_follows_content_size(True)

        settings = Gio.Settings.new(APP_ID)

        # General page
        page = Adw.PreferencesPage(title="General", icon_name="preferences-system-symbolic")
        self.add(page)

        # Refresh group
        refresh_group = Adw.PreferencesGroup(
            title="Refresh",
            description="How often to fetch usage data from the API.",
        )
        page.add(refresh_group)

        interval_row = Adw.SpinRow.new_with_range(15, 300, 5)
        interval_row.set_title("Refresh interval")
        interval_row.set_subtitle("Seconds between API requests")
        interval_row.set_value(settings.get_uint("refresh-interval"))
        interval_row.connect(
            "notify::value",
            lambda row, _: settings.set_uint("refresh-interval", int(row.get_value())),
        )
        refresh_group.add(interval_row)

        # Notifications group
        notify_group = Adw.PreferencesGroup(
            title="Notifications",
            description="Desktop notifications when session usage reaches these thresholds.",
        )
        page.add(notify_group)

        for threshold, key in [(75, "notify-at-75"), (90, "notify-at-90"), (95, "notify-at-95")]:
            row = Adw.SwitchRow(title=f"Notify at {threshold} %")
            row.set_active(settings.get_boolean(key))
            row.connect(
                "notify::active",
                lambda r, _, k=key: settings.set_boolean(k, r.get_active()),
            )
            notify_group.add(row)

        # Statusline group
        statusline_group = Adw.PreferencesGroup(
            title="Claude Code Statusline",
            description="Show usage in the Claude Code terminal status line.",
        )
        page.add(statusline_group)

        installed = DEFAULT_SCRIPT_PATH.exists()
        self._statusline_row = Adw.SwitchRow(title="Enable statusline")
        self._statusline_row.set_subtitle(
            str(DEFAULT_SCRIPT_PATH) if installed else "Installs a bash script to ~/.claude/"
        )
        self._statusline_row.set_active(installed)
        self._statusline_handler_id = self._statusline_row.connect(
            "notify::active", self._on_statusline_toggled
        )
        statusline_group.add(self._statusline_row)

    def _on_statusline_toggled(self, row, _param):
        try:
            if row.get_active():
                install_statusline()
                row.set_subtitle(str(DEFAULT_SCRIPT_PATH))
            else:
                uninstall_statusline()
                row.set_subtitle("Installs a bash script to ~/.claude/")
        except (OSError, BrokenSymlinkError, CorruptSettingsError) as exc:
            # Block the signal to avoid re-entrant calls while reverting.
            row.handler_block(self._statusline_handler_id)
            row.set_active(not row.get_active())
            row.handler_unblock(self._statusline_handler_id)
            toast = Adw.Toast(title=f"Statusline error: {exc}")
            self.add_toast(toast)
