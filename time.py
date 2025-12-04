from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET_ZONE = ZoneInfo("America/New_York")

def utc_to_eastern(utc_dt: datetime | None) -> datetime | None:
    """Convert UTC datetime to Eastern Time (ET/EDT automatically)."""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(ET_ZONE)

def format_et(dt_val):
    """Format datetime (string or object) as Eastern Time string."""
    if dt_val is None:
        return ""
    if isinstance(dt_val, str):
        try:
            dt = datetime.fromisoformat(dt_val)
        except Exception:
            return str(dt_val)
    else:
        dt = dt_val
    edt = utc_to_eastern(dt)
    return edt.strftime("%Y-%m-%d %I:%M %p ET") if edt else str(dt_val)
