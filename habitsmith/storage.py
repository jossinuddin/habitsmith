import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

ROOT = os.path.dirname(os.path.dirname(__file__))
HABITS_DIR = os.path.join(ROOT, "data", "habits")

def _ensure_dirs():
    os.makedirs(HABITS_DIR, exist_ok=True)

def _today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# --- snippet: normalize_habit ---
def normalize_habit(name: str) -> str:
    """Простейшая нормализация имени привычки."""
    return " ".join(name.strip().lower().split())
# --- endsnippet ---

def track(habit: str, value: int = 1, note: Optional[str] = None) -> str:
    """
    Отмечает выполнение привычки за сегодня.
    value — целочисленное значение (например, кол-во повторений или минут).
    """
    _ensure_dirs()
    day_key = _today_key()
    path = os.path.join(HABITS_DIR, f"{day_key}.json")
    data: Dict[str, Any] = {"date": day_key, "entries": []}

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    entry = {
        "ts": datetime.now().isoformat(),
        "habit": habit,
        "value": int(value),
        "note": note or ""
    }
    data["entries"].append(entry)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return path

def list_days() -> List[str]:
    _ensure_dirs()
    files = [f for f in os.listdir(HABITS_DIR) if f.endswith(".json")]
    return sorted(files)

def read_day(filename: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(HABITS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# autosave 2025-10-06T11:21:13.264449
