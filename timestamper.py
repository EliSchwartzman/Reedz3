from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET_ZONE = ZoneInfo("America/New_York")

def utc_to_eastern(utc_dt: datetime | None) -> datetime | None:
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(ET_ZONE)

def format_et(dt_val):
    if dt_val is None:
        return ""
    if isinstance(dt_val, str):
        try:
            dt = datetime.fromisoformat(dt_val)
        except:
            return str(dt_val)
    else:
        dt = dt_val
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    edt = dt.astimezone(ET_ZONE)
    return edt.strftime("%Y-%m-%d %I:%M %p ET")
