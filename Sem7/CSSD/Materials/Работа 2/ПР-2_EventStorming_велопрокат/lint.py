"""Проверка формулировок по Таблице 1 пособия (нужен pymorphy3)."""
import sys
import pymorphy3
import yaml

m = yaml.safe_load(open(sys.argv[1] if len(sys.argv) > 1 else "model.yaml", encoding="utf-8"))
morph = pymorphy3.MorphAnalyzer()
bad = []

def any_tag(word, test):
    return any(test(p.tag) for p in morph.parse(word))

for s in m["steps"]:
    w = s["command"].split()[0]
    if not any_tag(w, lambda t: t.POS == "INFN"):
        bad.append(f"команда не в неопределённой форме: {s['command']}")
    t = s["trigger"]
    if "policy" in t and not (t["policy"].startswith("Когда ") and ", то " in t["policy"]):
        bad.append(f"политика не в форме «когда ..., то ...»: {t['policy']}")
    if "schedule" in t and not t["schedule"].startswith("По расписанию"):
        bad.append(f"политика по расписанию без слов «По расписанию»: {t['schedule']}")
    for e in s["events"]:
        if not any(any_tag(w, lambda tg: "PRTS" in tg or (tg.POS == "VERB" and tg.tense == "past"))
                   for w in e["text"].split()):
            bad.append(f"событие не в прошедшем времени: {e['text']}")
for a in m["aggregates"].values():
    p = morph.parse(a["name"].split()[0])[0]
    if p.tag.POS != "NOUN" or p.tag.number != "sing":
        bad.append(f"агрегат не существительное в ед. ч.: {a['name']}")
    if not a.get("invariants"):
        bad.append(f"у агрегата нет инварианта: {a['name']}")
for h in m["hotspots"]:
    if not h["text"].rstrip().endswith("?"):
        bad.append(f"горячая точка без вопроса: {h['text']}")
print("\n".join(bad) if bad else "формулировки соответствуют Таблице 1")
sys.exit(1 if bad else 0)
