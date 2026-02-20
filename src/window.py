"""Main window for Claude Usage."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from datetime import datetime, timezone

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from api_client import fetch_usage
from credential_reader import CredentialError, read_credentials
from usage_calculator import color_for_pct
from usage_model import UsageData


def _format_reset_time(dt: datetime | None) -> str:
    """Format a reset datetime as a human-readable countdown or timestamp."""
    if dt is None:
        return "—"
    now = datetime.now(timezone.utc)
    delta = dt - now
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return "now"

    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60

    if hours > 24:
        days = hours // 24
        return f"{days}d {hours % 24}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _apply_color_to_bar(bar: Gtk.LevelBar, pct: float | None):
    """Apply a CSS colour to a LevelBar based on usage percentage."""
    r, g, b = color_for_pct(pct)
    css = f"""levelbar block.filled {{
        background-color: rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, 1.0);
    }}"""
    provider = Gtk.CssProvider()
    provider.load_from_string(css)
    bar.get_style_context().add_provider(
        provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class ClaudeUsageWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Claude Usage")
        self.set_default_size(420, 520)

        self._timer_id = None
        self._notification_tracker = set()

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
        scroll = Gtk.ScrolledWindow(vexpand=True)
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

        # Status icon + title
        title_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            halign=Gtk.Align.CENTER,
        )
        title_label = Gtk.Label(label="Claude Usage")
        title_label.add_css_class("title-1")
        title_box.append(title_label)
        self._status_label = Gtk.Label(label="Loading…")
        self._status_label.add_css_class("dim-label")
        title_box.append(self._status_label)
        content_box.append(title_box)

        # Session usage group
        session_group = Adw.PreferencesGroup(title="Session (5-hour)")
        self._session_row, self._session_bar = self._make_metric_row(
            "Usage", "—"
        )
        self._session_reset_row = Adw.ActionRow(title="Resets in", subtitle="—")
        session_group.add(self._session_row)
        session_group.add(self._session_reset_row)
        content_box.append(session_group)

        # Weekly usage group
        weekly_group = Adw.PreferencesGroup(title="Weekly (7-day)")
        self._weekly_row, self._weekly_bar = self._make_metric_row(
            "Usage", "—"
        )
        self._weekly_reset_row = Adw.ActionRow(title="Resets", subtitle="—")
        weekly_group.add(self._weekly_row)
        weekly_group.add(self._weekly_reset_row)
        content_box.append(weekly_group)

        # Opus weekly usage group
        opus_group = Adw.PreferencesGroup(title="Opus (7-day)")
        self._opus_row, self._opus_bar = self._make_metric_row(
            "Usage", "—"
        )
        opus_group.add(self._opus_row)
        content_box.append(opus_group)
        self._opus_group = opus_group

        # Last updated
        self._updated_label = Gtk.Label(
            label="",
            halign=Gtk.Align.CENTER,
        )
        self._updated_label.add_css_class("dim-label")
        self._updated_label.add_css_class("caption")
        content_box.append(self._updated_label)

        # Initial fetch
        self._refresh()

        # Auto-refresh timer
        self._start_timer()

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

    def _get_refresh_interval(self) -> int:
        """Get refresh interval from GSettings, with fallback."""
        try:
            from gi.repository import Gio

            settings = Gio.Settings.new("com.github.sl.claude-usage")
            return max(15, min(300, settings.get_uint("refresh-interval")))
        except Exception:
            return 60

    def _start_timer(self):
        """Start the auto-refresh timer."""
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
        interval = self._get_refresh_interval()
        self._timer_id = GLib.timeout_add_seconds(interval, self._on_timer)

    def _on_timer(self) -> bool:
        """Timer callback. Returns True to keep the timer running."""
        self._refresh()
        return True

    def _on_refresh_clicked(self, _button):
        self._refresh()

    def _refresh(self):
        """Read credentials and fetch usage data."""
        self._status_label.set_text("Refreshing…")

        try:
            creds = read_credentials()
        except CredentialError as exc:
            self._show_error(str(exc))
            return

        if creds.is_expired:
            self._show_error("OAuth token has expired. Re-authenticate via Claude Code CLI.")
            return

        fetch_usage(creds.access_token, self._on_usage_result)

    def _on_usage_result(self, data: UsageData | None, error: str | None):
        """Callback from fetch_usage — runs on the GLib main thread."""
        if error:
            self._show_error(error)
            return

        self._update_ui(data)
        self._check_notifications(data)

    def _update_ui(self, data: UsageData):
        """Populate the UI with fresh usage data."""
        # Session
        if data.session_pct is not None:
            self._session_row.set_subtitle(f"{data.session_pct:.1f} %")
            self._session_bar.set_value(min(data.session_pct, 100))
            _apply_color_to_bar(self._session_bar, data.session_pct)
        else:
            self._session_row.set_subtitle("—")
            self._session_bar.set_value(0)

        self._session_reset_row.set_subtitle(
            _format_reset_time(data.session_resets_at)
        )

        # Weekly
        if data.weekly_pct is not None:
            self._weekly_row.set_subtitle(f"{data.weekly_pct:.1f} %")
            self._weekly_bar.set_value(min(data.weekly_pct, 100))
            _apply_color_to_bar(self._weekly_bar, data.weekly_pct)
        else:
            self._weekly_row.set_subtitle("—")
            self._weekly_bar.set_value(0)

        if data.weekly_resets_at:
            self._weekly_reset_row.set_subtitle(
                data.weekly_resets_at.strftime("%a %d %b %H:%M UTC")
            )
        else:
            self._weekly_reset_row.set_subtitle("—")

        # Opus
        if data.opus_pct is not None:
            self._opus_row.set_subtitle(f"{data.opus_pct:.1f} %")
            self._opus_bar.set_value(min(data.opus_pct, 100))
            _apply_color_to_bar(self._opus_bar, data.opus_pct)
            self._opus_group.set_visible(True)
        else:
            self._opus_group.set_visible(False)

        # Status + timestamp
        self._status_label.set_text("Connected")
        now = datetime.now().strftime("%H:%M:%S")
        self._updated_label.set_text(f"Last updated: {now}")

    def _show_error(self, message: str):
        """Display an error message in the status label."""
        self._status_label.set_text(f"Error: {message}")

    def _check_notifications(self, data: UsageData):
        """Send desktop notifications at configured thresholds."""
        if data.session_pct is None:
            return

        try:
            from gi.repository import Gio

            settings = Gio.Settings.new("com.github.sl.claude-usage")
            thresholds = []
            if settings.get_boolean("notify-at-75"):
                thresholds.append(75)
            if settings.get_boolean("notify-at-90"):
                thresholds.append(90)
            if settings.get_boolean("notify-at-95"):
                thresholds.append(95)
        except Exception:
            thresholds = [75, 90, 95]

        app = self.get_application()
        if not app:
            return

        for threshold in thresholds:
            if data.session_pct >= threshold and threshold not in self._notification_tracker:
                self._notification_tracker.add(threshold)
                from gi.repository import Gio

                notification = Gio.Notification.new(f"Claude Usage: {data.session_pct:.0f} %")
                notification.set_body(
                    f"Session usage has reached {threshold} %. "
                    f"Resets {_format_reset_time(data.session_resets_at)}."
                )
                app.send_notification(f"threshold-{threshold}", notification)

        # Reset tracker when usage drops (after a reset)
        if data.session_pct < 50:
            self._notification_tracker.clear()
