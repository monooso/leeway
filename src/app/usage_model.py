# usage_model.py
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

"""Data classes for usage data."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class UsageData:
    """Parsed API usage data."""

    session_pct: float | None = None
    session_resets_at: datetime | None = None
    weekly_pct: float | None = None
    weekly_resets_at: datetime | None = None
    opus_pct: float | None = None
    opus_resets_at: datetime | None = None


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Handle both "Z" suffix and "+00:00"
        text = value.replace("Z", "+00:00")
        result = datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None
    # Reject naive datetimes (e.g. bare "2026-02-20" with no time/tz).
    if result.tzinfo is None:
        return None
    return result


def _get_pct(bucket: dict) -> float | None:
    """Get the utilisation percentage, trying both field names."""
    # The API uses "utilization_pct" in some responses and "utilization" in others.
    pct = bucket.get("utilization_pct")
    if pct is None:
        pct = bucket.get("utilization")
    return pct


def parse_usage_response(raw: dict) -> UsageData:
    """Parse the API JSON response into a UsageData instance.

    Args:
        raw: Decoded JSON dict from the usage endpoint.

    Returns:
        UsageData with whatever fields are present.
    """
    five_hour = raw.get("five_hour", {})
    seven_day = raw.get("seven_day", {})
    seven_day_opus = raw.get("seven_day_opus")

    return UsageData(
        session_pct=_get_pct(five_hour),
        session_resets_at=_parse_iso_datetime(five_hour.get("resets_at")),
        weekly_pct=_get_pct(seven_day),
        weekly_resets_at=_parse_iso_datetime(seven_day.get("resets_at")),
        opus_pct=_get_pct(seven_day_opus) if seven_day_opus else None,
        opus_resets_at=_parse_iso_datetime(seven_day_opus.get("resets_at")) if seven_day_opus else None,
    )
