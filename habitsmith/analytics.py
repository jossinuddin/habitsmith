from __future__ import annotations
import os, json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from .storage import HABITS_DIR

def _iter_last_days(n: int) -> List[str]:
    today = datetime.now().date()
    days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]
    return list(reversed(days))

def _read_json_by_day(day_key: str):
    path = os.path.join(HABITS_DIR, f"{day_key}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def weekly_stats(days: int = 7) -> Dict[str, Any]:
    """
    Агрегаты за последние N дней: сумма значений по привычкам, значения по дням,
    лучшая серия дней, где суммарное значение > 0.
    """
    habits: Dict[str, int] = {}
    total_value = 0
    per_day: List[Tuple[str, int]] = []

    for d in _iter_last_days(days):
        data = _read_json_by_day(d)
        day_total = 0
        if data and data.get("entries"):
            for e in data["entries"]:
                val = int(e.get("value", 0))
                name = e.get("habit", "unspecified")
                total_value += val
                day_total += val
                habits[name] = habits.get(name, 0) + val
        per_day.append((d, day_total))

    # Лучшая серия дней, где суммарно что-то сделали (>0)
    best_streak = 0
    cur = 0
    for _, m in per_day:
        if m > 0:
            cur += 1
            best_streak = max(best_streak, cur)
        else:
            cur = 0

    habits_sorted = dict(sorted(habits.items(), key=lambda x: -x[1]))
    return {
        "total_value": total_value,
        "habits": habits_sorted,
        "per_day": per_day,
        "best_streak_days": best_streak
    }
