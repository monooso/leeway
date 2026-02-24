# tests/test_usage_calculator.py
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

"""Tests for usage_calculator colour mappings."""

from math import isclose

from usage_calculator import STATUS_COLORS, StatusLevel


def _hex_to_floats(hex_color: str) -> tuple[float, float, float]:
    """Convert a hex colour string like '#33D17A' to an (R, G, B) float tuple."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


# GNOME HIG standard palette.
GNOME_GREEN = "#33D17A"
GNOME_YELLOW = "#F6D32D"
GNOME_RED = "#C01C28"


def _assert_color_matches(actual: tuple[float, float, float], expected_hex: str):
    """Assert each RGB channel matches the expected hex value within rounding tolerance."""
    expected = _hex_to_floats(expected_hex)
    for i, channel in enumerate(("R", "G", "B")):
        assert isclose(actual[i], expected[i], abs_tol=0.01), (
            f"{channel}: {actual[i]:.3f} != {expected[i]:.3f} (from {expected_hex})"
        )


class TestStatusColors:
    def test_safe_is_gnome_green(self):
        _assert_color_matches(STATUS_COLORS[StatusLevel.SAFE], GNOME_GREEN)

    def test_moderate_is_gnome_yellow(self):
        _assert_color_matches(STATUS_COLORS[StatusLevel.MODERATE], GNOME_YELLOW)

    def test_critical_is_gnome_red(self):
        _assert_color_matches(STATUS_COLORS[StatusLevel.CRITICAL], GNOME_RED)

