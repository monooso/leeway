# window.py
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

"""Main window for Leeway."""

from datetime import datetime, timezone

from gi.repository import Adw, Gio, GLib, Gtk

from .usage_group import LeewayUsageGroup  # noqa: F401 — registers the GType
from .api_client import fetch_usage
from .config import APP_ID
from .credential_reader import CredentialError, read_credentials
from .usage_calculator import color_for_pct
from .usage_model import UsageData


def _format_reset_time(dt: datetime | None, *, now: datetime | None = None) -> str:
    """Format a reset datetime as a human-readable countdown or timestamp."""
    if dt is None:
        return "\u2014"
    if now is None:
        now = datetime.now(timezone.utc)
    delta = dt - now
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return "now"

    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60

    if hours >= 24:
        days = hours // 24
        return f"{days}d {hours % 24}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m"
    return "< 1m"


def _truncate_error(message: str, *, max_length: int = 120) -> str:
    """Truncate an error message to a sensible display length."""
    if len(message) <= max_length:
        return message
    return message[: max_length - 3] + "..."


def _apply_color_to_bar(
    bar: Gtk.LevelBar,
    pct: float,
    bar_css: dict[Gtk.LevelBar, tuple[str, Gtk.CssProvider]],
):
    """Apply a CSS colour to a LevelBar based on usage percentage."""
    if bar in bar_css:
        css_class, old_provider = bar_css[bar]
        Gtk.StyleContext.remove_provider_for_display(
            bar.get_display(), old_provider
        )
    else:
        css_class = f"usage-bar-{len(bar_css)}"
        bar.add_css_class(css_class)

    r, g, b = color_for_pct(pct)
    css = (
        f"levelbar.{css_class} block.filled {{"
        f" background-color: rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, 1.0);"
        f" }}"
    )
    provider = Gtk.CssProvider()
    provider.load_from_string(css)
    Gtk.StyleContext.add_provider_for_display(
        bar.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    bar_css[bar] = (css_class, provider)


def _strip_default_offsets(bar: Gtk.LevelBar):
    """Remove the default GTK level bar offsets so we can colour it ourselves."""
    bar.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_LOW)
    bar.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_HIGH)
    bar.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_FULL)


@Gtk.Template(resource_path='/me/stephenlewis/Leeway/window.ui')
class LeewayWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'LeewayWindow'

    refresh_button = Gtk.Template.Child()
    session_group = Gtk.Template.Child()
    weekly_group = Gtk.Template.Child()
    opus_group = Gtk.Template.Child()
    status_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._timer_id = None
        self._debounce_id = None
        self._notification_tracker = set()
        self._cancellable = Gio.Cancellable()
        self._bar_css: dict[Gtk.LevelBar, tuple[str, Gtk.CssProvider]] = {}

        # Remove default level bar offsets (can't be done in XML)
        _strip_default_offsets(self.session_group.bar)
        _strip_default_offsets(self.weekly_group.bar)
        _strip_default_offsets(self.opus_group.bar)

        # Wire up the refresh button
        self.refresh_button.connect("clicked", self._on_refresh_clicked)

        # Listen for settings changes to restart the timer
        self._settings = Gio.Settings.new(APP_ID)
        self._settings.connect("changed::refresh-interval", self._on_interval_changed)

        # Initial fetch and auto-refresh timer
        self._refresh()
        self._start_timer()

    def do_close_request(self):
        """Clean up resources before the window is destroyed."""
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None
        if self._debounce_id is not None:
            GLib.source_remove(self._debounce_id)
            self._debounce_id = None
        self._cancellable.cancel()
        for _bar, (_, provider) in self._bar_css.items():
            Gtk.StyleContext.remove_provider_for_display(
                self.get_display(), provider
            )
        self._bar_css.clear()
        return Adw.ApplicationWindow.do_close_request(self)

    def refresh(self):
        """Public entry point for triggering a refresh (e.g. from app action)."""
        self._refresh()

    def _get_refresh_interval(self) -> int:
        """Get refresh interval from GSettings, with fallback."""
        try:
            return max(15, min(300, self._settings.get_uint("refresh-interval")))
        except GLib.Error:
            return 60

    def _start_timer(self):
        """Start the auto-refresh timer."""
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
        interval = self._get_refresh_interval()
        self._timer_id = GLib.timeout_add_seconds(interval, self._on_timer)

    def _on_interval_changed(self, _settings, _key):
        """Restart the timer when the refresh interval changes (debounced)."""
        if self._debounce_id is not None:
            GLib.source_remove(self._debounce_id)
        self._debounce_id = GLib.timeout_add(300, self._apply_interval_change)

    def _apply_interval_change(self) -> bool:
        """Actually restart the timer after the debounce delay."""
        self._debounce_id = None
        self._start_timer()
        return GLib.SOURCE_REMOVE

    def _on_timer(self) -> bool:
        """Timer callback. Returns True to keep the timer running."""
        self._refresh()
        return True

    def _on_refresh_clicked(self, _button):
        self._refresh()

    def _refresh(self):
        """Read credentials and fetch usage data."""
        self.status_label.set_text("Refreshing\u2026")

        try:
            creds = read_credentials()
        except CredentialError as exc:
            self._show_error(str(exc))
            return

        if creds.is_expired:
            self._show_error("OAuth token has expired. Re-authenticate via Claude Code CLI.")
            return

        # Cancel any in-flight request before starting a new one.
        self._cancellable.cancel()
        self._cancellable = Gio.Cancellable()

        fetch_usage(creds.access_token, self._on_usage_result, self._cancellable)

    def _on_usage_result(self, data: UsageData | None, error: str | None):
        """Callback from fetch_usage — runs on the GLib main thread."""
        if error:
            self._show_error(error)
            return

        if data is None:
            self._show_error("No data received")
            return

        self._update_ui(data)
        self._check_notifications(data)

    def _update_ui(self, data: UsageData):
        """Populate the UI with fresh usage data."""
        # Session
        if data.session_pct is not None:
            self.session_group.row.set_subtitle(f"{data.session_pct:.1f} %")
            self.session_group.bar.set_value(min(data.session_pct, 100))
            _apply_color_to_bar(self.session_group.bar, data.session_pct, self._bar_css)
        else:
            self.session_group.row.set_subtitle("\u2014")
            self.session_group.bar.set_value(0)

        reset_text = _format_reset_time(data.session_resets_at)
        if data.session_resets_at is not None:
            self.session_group.reset_label.set_label(f"Resets in {reset_text}")
        else:
            self.session_group.reset_label.set_label("")

        # Weekly
        if data.weekly_pct is not None:
            self.weekly_group.row.set_subtitle(f"{data.weekly_pct:.1f} %")
            self.weekly_group.bar.set_value(min(data.weekly_pct, 100))
            _apply_color_to_bar(self.weekly_group.bar, data.weekly_pct, self._bar_css)
        else:
            self.weekly_group.row.set_subtitle("\u2014")
            self.weekly_group.bar.set_value(0)

        weekly_reset_text = _format_reset_time(data.weekly_resets_at)
        if data.weekly_resets_at is not None:
            self.weekly_group.reset_label.set_label(f"Resets in {weekly_reset_text}")
        else:
            self.weekly_group.reset_label.set_label("")

        # Opus
        if data.opus_pct is not None:
            self.opus_group.row.set_subtitle(f"{data.opus_pct:.1f} %")
            self.opus_group.bar.set_value(min(data.opus_pct, 100))
            _apply_color_to_bar(self.opus_group.bar, data.opus_pct, self._bar_css)

            opus_reset_text = _format_reset_time(data.opus_resets_at)
            if data.opus_resets_at is not None:
                self.opus_group.reset_label.set_label(f"Resets in {opus_reset_text}")
            else:
                self.opus_group.reset_label.set_label("")

            self.opus_group.set_visible(True)
        else:
            self.opus_group.set_visible(False)

        # Footer
        now = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
        self.status_label.set_text(f"Connected \u00b7 Updated {now}")

    def _show_error(self, message: str):
        """Display an error message in the status label."""
        self.status_label.set_text(f"Error: {_truncate_error(message)}")

    def _check_notifications(self, data: UsageData):
        """Send desktop notifications when session usage crosses thresholds.

        Only session usage is tracked for notifications. Session limits reset
        every 5 hours and are the most immediately actionable; weekly limits
        are informational and shown in the dashboard but do not trigger alerts.
        """
        if data.session_pct is None:
            return

        try:
            thresholds = []
            if self._settings.get_boolean("notify-at-75"):
                thresholds.append(75)
            if self._settings.get_boolean("notify-at-90"):
                thresholds.append(90)
            if self._settings.get_boolean("notify-at-95"):
                thresholds.append(95)
        except GLib.Error:
            thresholds = [75, 90, 95]

        app = self.get_application()
        if not app:
            return

        for threshold in thresholds:
            if data.session_pct >= threshold and threshold not in self._notification_tracker:
                self._notification_tracker.add(threshold)

                reset_text = _format_reset_time(data.session_resets_at)
                if reset_text == "now":
                    body = f"Session usage has reached {threshold} %. Resets now."
                else:
                    body = f"Session usage has reached {threshold} %. Resets in {reset_text}."

                notification = Gio.Notification.new(f"Leeway: {data.session_pct:.0f} %")
                notification.set_body(body)
                app.send_notification(f"threshold-{threshold}", notification)

        # Reset tracker when usage drops below 50% (i.e. after a session reset),
        # so that notifications fire again for the new session.
        if data.session_pct < 50:
            self._notification_tracker.clear()
