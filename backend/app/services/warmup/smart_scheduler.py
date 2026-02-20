"""Smart Send Scheduling - human-like send timing."""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from sqlalchemy.orm import Session

from app.db.models.settings import Settings


def _get_setting(db: Session, key: str, default=None):
    setting = db.query(Settings).filter(Settings.key == key).first()
    if setting and setting.value_json:
        try:
            return json.loads(setting.value_json)
        except Exception:
            pass
    return default


def get_send_window(db: Session) -> Dict[str, Any]:
    start = _get_setting(db, "warmup_send_window_start", "09:00")
    end = _get_setting(db, "warmup_send_window_end", "17:00")
    tz = _get_setting(db, "warmup_timezone", "US/Eastern")
    return {"start": start, "end": end, "timezone": tz}


def calculate_send_times(count: int, db: Session) -> List[datetime]:
    window = get_send_window(db)
    start_h, start_m = map(int, window["start"].split(":"))
    end_h, end_m = map(int, window["end"].split(":"))

    now = datetime.utcnow()
    base = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end_time = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    total_minutes = int((end_time - base).total_seconds() / 60)

    if count <= 0 or total_minutes <= 0:
        return []

    min_gap = int(_get_setting(db, "warmup_min_gap_minutes", 15))
    max_gap = int(_get_setting(db, "warmup_max_gap_minutes", 60))

    times = []
    current = base + timedelta(minutes=random.randint(0, min(30, total_minutes)))
    for _ in range(count):
        if current > end_time:
            break
        times.append(add_human_jitter(current))
        gap = random.randint(min_gap, max_gap)
        current += timedelta(minutes=gap)

    return times


def add_human_jitter(timestamp: datetime, max_jitter_seconds: int = 120) -> datetime:
    jitter = random.randint(-max_jitter_seconds, max_jitter_seconds)
    return timestamp + timedelta(seconds=jitter)


def should_skip_weekend(db: Session) -> bool:
    skip = _get_setting(db, "warmup_skip_weekends", True)
    if skip:
        today = datetime.utcnow().weekday()
        return today >= 5
    return False
