"""
Ticket sahiplenme istatistikleri için basit JSON veritabanı
"""

import json
import os

TICKET_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tickets.json")


def _ensure_data_dir():
    data_dir = os.path.dirname(TICKET_DB_PATH)
    os.makedirs(data_dir, exist_ok=True)


def _load() -> dict:
    _ensure_data_dir()
    if not os.path.exists(TICKET_DB_PATH):
        return {}
    try:
        with open(TICKET_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save(data: dict):
    _ensure_data_dir()
    with open(TICKET_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_ticket_claim(user_id: str, guild_id: str):
    """Bir kullanıcının ticket sahiplenme sayısını artırır"""
    db = _load()
    key = f"{guild_id}_{user_id}"
    
    if key not in db:
        db[key] = {"count": 0}
    
    db[key]["count"] = db[key].get("count", 0) + 1
    _save(db)


def get_ticket_leaderboard(guild_id: str) -> list[tuple[str, int]]:
    """
    Sunucu için ticket sıralamasını döndürür
    Returns: [(user_id, count), ...] en çoktan aza sıralı
    """
    db = _load()
    prefix = f"{guild_id}_"
    
    results = []
    for key, value in db.items():
        if key.startswith(prefix):
            user_id = key[len(prefix):]
            count = value.get("count", 0)
            results.append((user_id, count))
    
    # En çoktan aza sırala
    results.sort(key=lambda x: x[1], reverse=True)
    return results
