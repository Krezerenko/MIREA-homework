"""Статистика demos.tf для расчёта нагрузки записи (лист «4 Расчёт нагрузки», B31 и B32).

Что считает по каждому дню (UTC):
  - число демок (= матчей, выгруженных за сутки);
  - число уникальных игроков;
  - средние игроков в матче и длительность матча;
И по выборке файлов: средний и медианный размер демки (HEAD-запрос, скачивать не нужно).

Неполные дни (первый и последний в выборке) отбрасываются: в прошлой версии
значения 855 и 1208 занижены именно поэтому.
"""
import csv
import statistics
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://api.demos.tf"
PAGES = 100
WORKERS = 6
SIZE_SAMPLE = 300

session = requests.Session()
session.headers["User-Agent"] = "StudentProjectDemoStats/2.0"
retry = Retry(total=4, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=WORKERS))


def fetch_list(pages):
    demos = []
    for page in range(1, pages + 1):
        r = session.get(f"{API}/demos", params={"page": page}, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        demos.extend(batch)
        print(f"страница {page}: {len(batch)}")
    return demos


def fetch_players(demo_id):
    r = session.get(f"{API}/demos/{demo_id}", timeout=30)
    r.raise_for_status()
    return demo_id, [p["user_id"] for p in r.json().get("players", [])]


def fetch_size_mb(url):
    r = session.head(url, allow_redirects=True, timeout=30)
    length = r.headers.get("Content-Length")
    return int(length) / 1024 / 1024 if length else None


def main():
    t0 = time.time()
    demos = fetch_list(PAGES)

    players = {}
    with ThreadPoolExecutor(WORKERS) as pool:
        futures = [pool.submit(fetch_players, d["id"]) for d in demos]
        for i, f in enumerate(as_completed(futures), 1):
            try:
                demo_id, ids = f.result()
                players[demo_id] = ids
            except Exception as e:
                print("пропуск:", e)
            if i % 200 == 0:
                print(f"детали: {i}/{len(futures)}")

    days = defaultdict(lambda: {"demos": 0, "players": set(), "pc": [], "dur": []})
    for d in demos:
        day = datetime.fromtimestamp(int(d["time"]), tz=timezone.utc).strftime("%Y-%m-%d")
        s = days[day]
        s["demos"] += 1
        s["players"].update(players.get(d["id"], []))
        if d.get("playerCount"):
            s["pc"].append(d["playerCount"])
        if d.get("duration"):
            s["dur"].append(d["duration"] / 60)

    full_days = sorted(days)[1:-1]
    with open("demos_by_day.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["день", "демок", "уникальных игроков", "игроков в матче, ср.", "длительность, мин, ср."])
        for day in full_days:
            s = days[day]
            w.writerow([day, s["demos"], len(s["players"]),
                        round(statistics.mean(s["pc"]), 1) if s["pc"] else "",
                        round(statistics.mean(s["dur"]), 1) if s["dur"] else ""])

    urls = [d["url"] for d in demos if d.get("url")][:SIZE_SAMPLE]
    with ThreadPoolExecutor(WORKERS) as pool:
        sizes = [s for s in pool.map(lambda u: _safe(fetch_size_mb, u), urls) if s]

    all_pc = [x for day in full_days for x in days[day]["pc"]]
    print("\n=== Итог для листа «4 Расчёт нагрузки» ===")
    print(f"полных дней: {len(full_days)}")
    print(f"демок в сутки, ср.: {statistics.mean(days[d]['demos'] for d in full_days):.0f}")
    print(f"уникальных игроков в сутки, ср.: {statistics.mean(len(days[d]['players']) for d in full_days):.0f}")
    if all_pc:
        print(f"B31, игроков в матче, ср.: {statistics.mean(all_pc):.1f}")
    if sizes:
        print(f"B32, размер демки, МБ: среднее {statistics.mean(sizes):.1f}, "
              f"медиана {statistics.median(sizes):.1f}, p95 {sorted(sizes)[int(len(sizes) * 0.95) - 1]:.1f} "
              f"(выборка {len(sizes)})")
    print(f"время работы: {time.time() - t0:.0f} с; по дням см. demos_by_day.csv")


def _safe(fn, arg):
    try:
        return fn(arg)
    except Exception:
        return None


if __name__ == "__main__":
    main()
