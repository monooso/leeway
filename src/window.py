"""Main window for Claude Usage."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from datetime import datetime, timezone

from gi.repository import Adw, Gio, GLib, Gtk

from api_client import fetch_usage
from config import APP_ID
from credential_reader import CredentialError, read_credentials
from usage_calculator import color_for_pct
from usage_model import UsageData


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
        return f"{days}d {hours % 24}h"
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
    pct: float | None,
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


class ClaudeUsageWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Claude Usage")
        self.set_default_size(420, -1)

        self._timer_id = None
        self._debounce_id = None
        self._notification_tracker = set()
        self._cancellable = Gio.Cancellable()
        self._bar_css: dict[Gtk.LevelBar, tuple[str, Gtk.CssProvider]] = {}

        # Main layout
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        # Header bar with refresh button and menu
        header = Adw.HeaderBar()

        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Refresh")
        refresh_btn.connect("clicked", self._on_refresh_clicked)
        header.pack_start(refresh_btn)

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic", tooltip_text="Menu")
        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("About", "app.about")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        toolbar_view.add_top_bar(header)

        # Scrollable content
        scroll = Gtk.ScrolledWindow(vexpand=True, propagate_natural_height=True)
        toolbar_view.set_content(scroll)

        content_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=24,
            margin_top=24,
            margin_bottom=24,
            margin_start=24,
            margin_end=24,
        )
        scroll.set_child(content_box)

        # Session usage group
        session_group = Adw.PreferencesGroup(title="Session (5-hour)")
        self._session_reset_label = self._make_header_suffix(session_group)
        self._session_row, self._session_bar = self._make_metric_row(
            "Usage", "\u2014"
        )
        session_group.add(self._session_row)
        content_box.append(session_group)

        # Weekly usage group
        weekly_group = Adw.PreferencesGroup(title="Weekly (7-day)")
        self._weekly_reset_label = self._make_header_suffix(weekly_group)
        self._weekly_row, self._weekly_bar = self._make_metric_row(
            "Usage", "\u2014"
        )
        weekly_group.add(self._weekly_row)
        content_box.append(weekly_group)

        # Opus weekly usage group
        opus_group = Adw.PreferencesGroup(title="Opus (7-day)")
        self._opus_row, self._opus_bar = self._make_metric_row(
            "Usage", "\u2014"
        )
        opus_group.add(self._opus_row)
        opus_group.set_visible(False)
        content_box.append(opus_group)
        self._opus_group = opus_group

        # Status footer
        self._status_label = Gtk.Label(
            label="Loading\u2026",
            halign=Gtk.Align.CENTER,
            margin_top=12,
        )
        self._status_label.add_css_class("dim-label")
        self._status_label.add_css_class("caption")

        content_box.append(self._status_label)

        # Listen for settings changes to restart the timer
        self._settings = Gio.Settings.new(APP_ID)
        self._settings.connect("changed::refresh-interval", self._on_interval_changed)

        # Initial fetch
        self._refresh()

        # Auto-refresh timer
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

    def _make_metric_row(
        self, title: str, subtitle: str
    ) -> tuple[Adw.ActionRow, Gtk.LevelBar]:
        """Create an ActionRow with an embedded LevelBar."""
        row = Adw.ActionRow(title=title, subtitle=subtitle)

        bar = Gtk.LevelBar()
        bar.set_min_value(0)
        bar.set_max_value(100)
        bar.set_value(0)
        bar.set_valign(Gtk.Align.CENTER)
        bar.set_hexpand(True)
        bar.set_size_request(120, -1)
        # Remove the default offset styling so we can colour it ourselves
        bar.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_LOW)
        bar.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_HIGH)
        bar.remove_offset_value(Gtk.LEVEL_BAR_OFFSET_FULL)

        row.add_suffix(bar)
        return row, bar

    def _make_header_suffix(self, group: Adw.PreferencesGroup) -> Gtk.Label:
        """Add a right-aligned reset-time label to a PreferencesGroup header."""
        label = Gtk.Label(label="")
        label.add_css_class("dim-label")
        label.set_valign(Gtk.Align.CENTER)
        group.set_header_suffix(label)
        return label

    def _get_refresh_interval(self) -> int:
        """Get refresh interval from GSettings, with fallback."""
        try:
            return max(15, min(300, self._settings.get_uint("refresh-interval")))
        except Exception:
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
        self._status_label.set_text("Refreshing\u2026")

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
            self._session_row.set_subtitle(f"{data.session_pct:.1f} %")
            self._session_bar.set_value(min(data.session_pct, 100))
            _apply_color_to_bar(self._session_bar, data.session_pct, self._bar_css)
        else:
            self._session_row.set_subtitle("\u2014")
            self._session_bar.set_value(0)

        reset_text = _format_reset_time(data.session_resets_at)
        if data.session_resets_at is not None:
            self._session_reset_label.set_label(f"Resets in {reset_text}")
        else:
            self._session_reset_label.set_label("")

        # Weekly
        if data.weekly_pct is not None:
            self._weekly_row.set_subtitle(f"{data.weekly_pct:.1f} %")
            self._weekly_bar.set_value(min(data.weekly_pct, 100))
            _apply_color_to_bar(self._weekly_bar, data.weekly_pct, self._bar_css)
        else:
            self._weekly_row.set_subtitle("\u2014")
            self._weekly_bar.set_value(0)

        if data.weekly_resets_at:
            local_reset = data.weekly_resets_at.astimezone()
            self._weekly_reset_label.set_label(
                f"Resets {local_reset.strftime('%a %d %b %H:%M')}"
            )
        else:
            self._weekly_reset_label.set_label("")

        # Opus
        if data.opus_pct is not None:
            self._opus_row.set_subtitle(f"{data.opus_pct:.1f} %")
            self._opus_bar.set_value(min(data.opus_pct, 100))
            _apply_color_to_bar(self._opus_bar, data.opus_pct, self._bar_css)
            self._opus_group.set_visible(True)
        else:
            self._opus_group.set_visible(False)

        # Footer
        now = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
        self._status_label.set_text(f"Connected \u00b7 Updated {now}")

    def _show_error(self, message: str):
        """Display an error message in the status label."""
        self._status_label.set_text(f"Error: {_truncate_error(message)}")

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
        except Exception:
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

                notification = Gio.Notification.new(f"Claude Usage: {data.session_pct:.0f} %")
                notification.set_body(body)
                app.send_notification(f"threshold-{threshold}", notification)

        # Reset tracker when usage drops below 50% (i.e. after a session reset),
        # so that notifications fire again for the new session.
        if data.session_pct < 50:
            self._notification_tracker.clear()
