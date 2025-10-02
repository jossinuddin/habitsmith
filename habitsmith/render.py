import os
from datetime import datetime
from .analytics import weekly_stats

ROOT = os.path.dirname(os.path.dirname(__file__))
REPORTS_DIR = os.path.join(ROOT, "reports")

def render_weekly_report(days: int = 7) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stats = weekly_stats(days=days)
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    fname = os.path.join(REPORTS_DIR, f"weekly_{now}.md")

    lines = []
    lines.append(f"# HabitSmith — отчёт за {days} дней\n")
    lines.append(f"- Суммарное значение (все привычки): **{stats['total_value']}**")
    lines.append(f"- Лучшая серия (дней подряд > 0): **{stats['best_streak_days']}**\n")

    lines.append("## По привычкам (сумма значений)")
    if stats["habits"]:
        for name, total in stats["habits"].items():
            lines.append(f"- {name}: {total}")
    else:
        lines.append("_Нет данных_")

    lines.append("\n## По дням (суммарное значение)")
    for d, m in stats["per_day"]:
        lines.append(f"- {d}: {m}")

    content = "\n".join(lines) + "\n"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)
    return fname
