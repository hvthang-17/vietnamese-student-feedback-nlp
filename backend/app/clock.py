from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def now() -> datetime:
    return datetime.now(TZ)


