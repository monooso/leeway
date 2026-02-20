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
    # Handle both "Z" suffix and "+00:00"
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)


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
        session_pct=five_hour.get("utilization_pct"),
        session_resets_at=_parse_iso_datetime(five_hour.get("resets_at")),
        weekly_pct=seven_day.get("utilization_pct"),
        weekly_resets_at=_parse_iso_datetime(seven_day.get("resets_at")),
        opus_pct=seven_day_opus.get("utilization_pct") if seven_day_opus else None,
        opus_resets_at=_parse_iso_datetime(seven_day_opus.get("resets_at")) if seven_day_opus else None,
    )
