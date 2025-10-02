import random
import time
import subprocess
from datetime import datetime, timedelta

# универсальный импорт notify
try:
    from auto_updater.notify import notify
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
    from auto_updater.notify import notify

def run_updater():
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запускаю updater.py"
    print(msg)
    notify(msg)
    subprocess.run(["python3", "auto_updater/updater.py"])

def main():
    # 0–120 мин задержка от времени cron (например, 07:00 → реальный старт 07:00–09:00)
    delay = random.randint(0, 120 * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduler стартовал, задержка {delay//60} мин")
    notify(f"Scheduler стартовал, задержка {delay//60} мин")
    time.sleep(delay)

    # 0/1/2 запуска в день (веса 1:3:2)
    runs = random.choices([0, 1, 2], weights=[1, 3, 2])[0]
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Сегодня планируется {runs} запуск(ов)")
    notify(f"Сегодня планируется {runs} запуск(ов)")
    if runs == 0:
        notify("Сегодня запусков не будет")
        return

    # окно для запусков: 09:00–22:00
    start_sec = 9 * 3600
    end_sec = 22 * 3600

    run_times = sorted(random.sample(range(start_sec, end_sec), runs))
    run_hours = [(datetime.min + timedelta(seconds=t)).strftime("%H:%M") for t in run_times]
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Сегодня коммиты будут в: {', '.join(run_hours)}")
    notify(f"Сегодня коммиты будут в: {', '.join(run_hours)}")

    for t in run_times:
        now = datetime.now()
        target = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=t)
        wait_sec = (target - now).total_seconds()
        if wait_sec > 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ждём {int(wait_sec)} сек до {target.strftime('%H:%M:%S')}")
            time.sleep(wait_sec)
        run_updater()

    notify(f"Scheduler завершил работу, сегодня выполнено {runs} запуск(ов)")

if __name__ == "__main__":
    main()
