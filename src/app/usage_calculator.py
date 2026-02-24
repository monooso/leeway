# usage_calculator.py
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

"""Colour/status threshold calculations."""

from enum import Enum, auto

MODERATE_THRESHOLD = 50.0  # % — above this is moderate
CRITICAL_THRESHOLD = 80.0  # % — above this is critical


class StatusLevel(Enum):
    SAFE = auto()      # <= MODERATE_THRESHOLD
    MODERATE = auto()  # MODERATE_THRESHOLD < x <= CRITICAL_THRESHOLD
    CRITICAL = auto()  # > CRITICAL_THRESHOLD
    UNKNOWN = auto()   # No data


def status_for_pct(pct: float | None) -> StatusLevel:
    """Map a utilisation percentage to a status level."""
    if pct is None:
        return StatusLevel.UNKNOWN
    if pct <= MODERATE_THRESHOLD:
        return StatusLevel.SAFE
    if pct <= CRITICAL_THRESHOLD:
        return StatusLevel.MODERATE
    return StatusLevel.CRITICAL


# RGB tuples (0.0-1.0) for GTK colour properties.
# GNOME HIG standard palette: green #33D17A, yellow #F6D32D, red #C01C28.
STATUS_COLORS: dict[StatusLevel, tuple[float, float, float]] = {
    StatusLevel.SAFE: (0x33 / 255, 0xD1 / 255, 0x7A / 255),       # green
    StatusLevel.MODERATE: (0xF6 / 255, 0xD3 / 255, 0x2D / 255),   # yellow
    StatusLevel.CRITICAL: (0xC0 / 255, 0x1C / 255, 0x28 / 255),   # red
    StatusLevel.UNKNOWN: (0.50, 0.50, 0.50),                       # grey
}


def color_for_status(level: StatusLevel) -> tuple[float, float, float]:
    """Return an (R, G, B) tuple for the given status level."""
    return STATUS_COLORS[level]


def color_for_pct(pct: float | None) -> tuple[float, float, float]:
    """Convenience: map a percentage directly to a colour."""
    return color_for_status(status_for_pct(pct))
