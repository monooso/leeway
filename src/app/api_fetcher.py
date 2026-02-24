# api_fetcher.py
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

"""Async HTTP layer for fetching usage data via libsoup3."""

import gi

gi.require_version("Soup", "3.0")

from gi.repository import Gio, GLib, Soup

from .api_client import API_URL, ApiError, build_request_headers, parse_response_body

# Module-level session — reused across requests, avoids GC disposal warnings.
# Short idle timeout prevents stale keep-alive connections from causing
# "Socket I/O timed out" errors when the refresh interval elapses.
_session = Soup.Session()
_session.set_idle_timeout(10)


def fetch_usage(access_token: str, callback, cancellable: Gio.Cancellable | None = None):
    """Fetch usage data asynchronously using libsoup3.

    Args:
        access_token: OAuth Bearer token.
        callback: Called with (UsageData | None, str | None).
            On success: callback(data, None).
            On failure: callback(None, error_message).
        cancellable: Optional GCancellable to abort the request.
    """
    message = Soup.Message.new("GET", API_URL)

    headers = build_request_headers(access_token)
    request_headers = message.get_request_headers()
    for name, value in headers.items():
        request_headers.append(name, value)

    def on_response(_session, result):
        try:
            gbytes = _session.send_and_read_finish(result)
        except GLib.Error as exc:
            # Silently ignore cancellation — the window is closing.
            if exc.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                return
            callback(None, f"HTTP request failed: {exc.message}")
            return

        status = message.get_status()
        if status != Soup.Status.OK:
            phrase = Soup.Status.get_phrase(status)
            callback(None, f"API returned {int(status)}: {phrase}")
            return

        try:
            body = gbytes.get_data().decode("utf-8")
        except Exception as exc:
            callback(None, f"Failed to read response: {exc}")
            return

        try:
            data = parse_response_body(body)
        except ApiError as exc:
            callback(None, str(exc))
            return

        callback(data, None)

    _session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, cancellable, on_response)
