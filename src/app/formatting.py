# formatting.py
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

"""Pure formatting helpers for display strings."""

from datetime import datetime, timezone


def format_reset_time(dt: datetime | None, *, now: datetime | None = None) -> str:
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


def truncate_error(message: str, *, max_length: int = 120) -> str:
    """Truncate an error message to a sensible display length."""
    if len(message) <= max_length:
        return message
    return message[: max_length - 3] + "..."
