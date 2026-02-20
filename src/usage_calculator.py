"""Colour/status threshold calculations."""

from enum import Enum, auto


class StatusLevel(Enum):
    SAFE = auto()      # ≤50 %
    MODERATE = auto()  # 50–80 %
    CRITICAL = auto()  # >80 %
    UNKNOWN = auto()   # No data


def status_for_pct(pct: float | None) -> StatusLevel:
    """Map a utilisation percentage to a status level."""
    if pct is None:
        return StatusLevel.UNKNOWN
    if pct <= 50.0:
        return StatusLevel.SAFE
    if pct <= 80.0:
        return StatusLevel.MODERATE
    return StatusLevel.CRITICAL


# RGB tuples (0.0–1.0) for GTK colour properties.
_STATUS_COLORS: dict[StatusLevel, tuple[float, float, float]] = {
    StatusLevel.SAFE: (0.18, 0.80, 0.44),       # green
    StatusLevel.MODERATE: (0.95, 0.77, 0.06),    # amber
    StatusLevel.CRITICAL: (0.90, 0.24, 0.24),    # red
    StatusLevel.UNKNOWN: (0.50, 0.50, 0.50),     # grey
}


def color_for_status(level: StatusLevel) -> tuple[float, float, float]:
    """Return an (R, G, B) tuple for the given status level."""
    return _STATUS_COLORS[level]


def color_for_pct(pct: float | None) -> tuple[float, float, float]:
    """Convenience: map a percentage directly to a colour."""
    return color_for_status(status_for_pct(pct))
