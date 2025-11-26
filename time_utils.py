from datetime import datetime
from zoneinfo import ZoneInfo

ET_ZONE = ZoneInfo("America/New_York")

def utc_to_eastern(utc_dt: datetime) -> datetime:
    if not utc_dt:
        return None
    if utc_dt.tzinfo is None:
        from datetime import timezone
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(ET_ZONE)
