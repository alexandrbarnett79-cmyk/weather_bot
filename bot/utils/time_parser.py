"""Парсер пользовательского ввода времени для прогноза на конкретный момент.

Поддерживаются форматы:
  • "18:30", "в 18:30", "18" — ближайшее время (если уже прошло — завтра)
  • "сегодня 15", "завтра 18:30", "послезавтра 9:00"
  • "завтра утром/днём/вечером/ночью"
  • "через 3 часа", "через 30 минут"
  • "12.04 18:30", "12.04.2026 18:30"
  • "2026-04-10 18:30"
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta


_DAY_WORDS = {
    "послезавтра": 2,
    "завтра": 1,
    "сегодня": 0,
    "сейчас": 0,
}

_PARTS_OF_DAY = {
    "утром": 9,
    "утро": 9,
    "днем": 14,
    "день": 14,
    "вечером": 19,
    "вечер": 19,
    "ночью": 23,
    "ночь": 23,
}


def parse_user_time(text: str, now_local: datetime) -> datetime | None:
    """Парсит ввод пользователя и возвращает локальное datetime (naive, в той же tz, что now_local).

    Если распарсить не удалось — возвращает None.
    """
    if not text:
        return None
    t = text.strip().lower().replace("ё", "е")

    # --- 1. через N часов / минут ----------------------------------------
    m = re.search(r"через\s+(\d+)\s*(час\w*|ч|мин\w*|м)\b", t)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        delta = timedelta(hours=n) if unit.startswith(("час", "ч")) else timedelta(minutes=n)
        return now_local + delta

    # --- 2. ISO: 2026-04-10 [18[:30]] ------------------------------------
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ tT](\d{1,2})(?::(\d{2}))?)?", t)
    if m:
        y, mo, d, hh, mm = m.groups()
        hour = int(hh) if hh else 12
        minute = int(mm) if mm else 0
        try:
            return datetime(int(y), int(mo), int(d), hour, minute)
        except ValueError:
            return None

    # --- 3. DD.MM[.YYYY] [HH[:MM]] ---------------------------------------
    m = re.search(
        r"\b(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?(?:\s+(\d{1,2})(?::(\d{2}))?)?\b",
        t,
    )
    if m:
        d, mo, y, hh, mm = m.groups()
        d_i, mo_i = int(d), int(mo)
        # отсекаем вид "18.30" (хотят сказать 18:30) — там mo=30 > 12
        if 1 <= mo_i <= 12 and 1 <= d_i <= 31:
            year = now_local.year
            if y:
                year = int(y)
                if year < 100:
                    year += 2000
            hour = int(hh) if hh else 12
            minute = int(mm) if mm else 0
            try:
                return datetime(year, mo_i, d_i, hour, minute)
            except ValueError:
                pass

    # --- 4. Ключевые слова дня + время -----------------------------------
    day_offset: int | None = None
    t_rest = t
    for word, offset in _DAY_WORDS.items():
        if word in t_rest:
            day_offset = offset
            t_rest = t_rest.replace(word, " ")
            break

    pod_hour: int | None = None
    for word, hr in _PARTS_OF_DAY.items():
        if word in t_rest:
            pod_hour = hr
            t_rest = t_rest.replace(word, " ")
            break

    hour: int | None = None
    minute: int = 0
    tm = re.search(r"(?:в\s+)?(\d{1,2})(?:[:\.](\d{2}))?", t_rest)
    if tm:
        hh = int(tm.group(1))
        mm_raw = tm.group(2)
        mm = int(mm_raw) if mm_raw else 0
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            hour, minute = hh, mm

    if day_offset is None and hour is None and pod_hour is None:
        return None

    base = now_local + timedelta(days=day_offset or 0)
    if hour is not None:
        result = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif pod_hour is not None:
        result = base.replace(hour=pod_hour, minute=0, second=0, microsecond=0)
    else:
        result = base.replace(hour=12, minute=0, second=0, microsecond=0)

    # время без явной даты и уже прошло → переносим на завтра
    if day_offset is None and result <= now_local:
        result += timedelta(days=1)

    return result
