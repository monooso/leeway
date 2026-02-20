"""Main window for Claude Usage."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk


class ClaudeUsageWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Claude Usage")
        self.set_default_size(420, 520)

        # Placeholder content — replaced in Phase 6
        status_page = Adw.StatusPage(
            title="Claude Usage",
            description="Loading…",
            icon_name="dialog-information-symbolic",
        )
        self.set_content(status_page)
