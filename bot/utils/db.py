"""
Basit JSON tabanlı istatistik veritabanı.
Production için SQLite veya PostgreSQL kullanmanız önerilir.
"""

import json
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stats.json")


def _ensure_data_dir():
    data_dir = os.path.dirname(DB_PATH)
    os.makedirs(data_dir, exist_ok=True)


def _load() -> dict:
    _ensure_data_dir()
    if not os.path.exists(DB_PATH):
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save(data: dict):
    _ensure_data_dir()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _key(user_id: str, guild_id: str) -> str:
    return f"{guild_id}_{user_id}"


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _week_start() -> str:
    d = datetime.utcnow()
    start = d - timedelta(days=d.weekday())
    return start.strftime("%Y-%m-%d")


def _weekly_messages(daily: dict, week_start: str) -> int:
    total = 0
    start = datetime.strptime(week_start, "%Y-%m-%d")
    for i in range(7):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        total += daily.get(day, 0)
    return total


# ─── Public API ───────────────────────────────────────────────────────────────

def get_stats(user_id: str, guild_id: str) -> dict:
    db = _load()
    k = _key(user_id, guild_id)
    today = _today()
    week = _week_start()

    if k not in db:
        return {
            "messages": 0,
            "messages_today": 0,
            "messages_week": 0,
            "voice_minutes": 0,
            "voice_today": 0,
            "voice_week": 0,
        }

    u = db[k]
    daily_msg = u.get("daily_messages", {})
    daily_voice = u.get("daily_voice", {})

    return {
        "messages": u.get("messages", 0),
        "messages_today": daily_msg.get(today, 0),
        "messages_week": _weekly_messages(daily_msg, week),
        "voice_minutes": u.get("voice_minutes", 0),
        "voice_today": daily_voice.get(today, 0),
        "voice_week": _weekly_messages(daily_voice, week),
    }


def add_message(user_id: str, guild_id: str):
    db = _load()
    k = _key(user_id, guild_id)
    today = _today()

    if k not in db:
        db[k] = {}

    u = db[k]
    u["messages"] = u.get("messages", 0) + 1

    if "daily_messages" not in u:
        u["daily_messages"] = {}
    u["daily_messages"][today] = u["daily_messages"].get(today, 0) + 1

    # 30 günden eski verileri temizle
    cutoff = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    u["daily_messages"] = {
        d: v for d, v in u["daily_messages"].items() if d >= cutoff
    }

    _save(db)


def add_voice(user_id: str, guild_id: str, minutes: int):
    db = _load()
    k = _key(user_id, guild_id)
    today = _today()

    if k not in db:
        db[k] = {}

    u = db[k]
    u["voice_minutes"] = u.get("voice_minutes", 0) + minutes

    if "daily_voice" not in u:
        u["daily_voice"] = {}
    u["daily_voice"][today] = u["daily_voice"].get(today, 0) + minutes

    _save(db)
