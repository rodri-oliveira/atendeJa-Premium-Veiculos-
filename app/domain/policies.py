from __future__ import annotations
from datetime import datetime, time
from zoneinfo import ZoneInfo

# Simple business hours policy (configurable per-tenant in the future)
DEFAULT_TZ = ZoneInfo("America/Sao_Paulo")
DEFAULT_START = time(9, 0)
DEFAULT_END = time(0, 0)  # midnight (00:00)


def within_business_hours(
    now: datetime | None = None,
    tz: ZoneInfo = DEFAULT_TZ,
    start: time = DEFAULT_START,
    end: time = DEFAULT_END,
) -> bool:
    """
    Returns True if now is within [start, end). If end == 00:00, treat as until midnight.
    """
    now = now or datetime.now(tz)
    local_t = now.astimezone(tz).time()
    if start <= end and end != time(0, 0):
        return start <= local_t < end
    # Window crosses midnight or end is midnight (00:00 == full-day end)
    if end == time(0, 0):
        # Allow from start until 23:59:59
        return local_t >= start or local_t < time(0, 0)
    return local_t >= start or local_t < end
