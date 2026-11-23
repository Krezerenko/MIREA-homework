"""model.yaml -> PlantUML. Два вида: лента (--timeline) и группировка по контекстам (по умолчанию).

Раскладку считает Graphviz, поэтому лента и дорожки контекстов одновременно не получаются:
это второстепенный вид, основная карта собирается в draw.io.
"""
import sys

import yaml

SRC = sys.argv[1] if len(sys.argv) > 1 else "model.yaml"
OUT = sys.argv[2] if len(sys.argv) > 2 else "ES_velo_contexts.puml"
TIMELINE = "--timeline" in sys.argv
m = yaml.safe_load(open(SRC, encoding="utf-8"))

# элемент PlantUML, цвет, стиль линии, подпись типа
KIND = {
    "event":     ("rectangle", "#FFA940", "",            "событие"),
    "command":   ("rectangle", "#69B1FF", ";line.bold",  "команда"),
    "actor":     ("rectangle", "#FFF566", "",            "участник"),
    "agent":     ("rectangle", "#87E8DE", ";line.dotted", "ИИ-агент"),
    "aggregate": ("rectangle", "#FFE58F", ";line.bold",  "агрегат"),
    "policy":    ("rectangle", "#D3ADF7", ";line.dashed", "политика"),
    "schedule":  ("rectangle", "#D3ADF7", ";line.dashed", "политика, по расписанию"),
    "external":  ("node",      "#FFADD2", "",            "внешняя система"),
    "readmodel": ("file",      "#95DE64", "",            "модель чтения"),
    "hotspot":   ("hexagon",   "#FF7875", "",            "горячая точка"),
}

def node(kind, id_, text):
    el, color, line, cap = KIND[kind]
    body = text.replace('"', "'")
    if kind == "aggregate":                      # крупнее прочих: жирный кегль и поля
        body = f"<size:15><b>{body}</b></size>\\n "
        cap = " \\n<i><size:10>" + cap + "</size></i>"
    else:
        cap = "<i><size:10>" + cap + "</size></i>"
    stereo = " <<ai>>" if kind == "agent" else ""
    return f'{el} "{cap}\\n{body}" as {id_}{stereo} {color}{line}'

L = ["@startuml", "left to right direction",
     "skinparam defaultFontName Arial", "skinparam defaultFontSize 12",
     "skinparam shadowing false", "skinparam wrapWidth 130", "skinparam defaultTextAlignment center",
     "skinparam ArrowColor #333333", "skinparam rectangle {\n  BorderColor #1F1F1F\n}",
     "skinparam rectangle<<ai>> {\n  RoundCorner 25\n}",
     "skinparam rectangle<<ctx>> {\n  BorderStyle dashed\n  BorderColor #404040\n  BackgroundColor #FAFAFA\n"
     "  FontSize 15\n  FontStyle bold\n}",
     "hide stereotype", f"title {m['title']}", ""]

by_ctx = {c["id"]: [] for c in m["contexts"]}
arrows, ev_col = [], {}
for s in m["steps"]:
    sid, out, t = s["id"], by_ctx[s["ctx"]], s["trigger"]
    if "actor" in t:
        out.append(node("actor", f"{sid}_a", m["actors"][t["actor"]]))
        base = s["col"]
    elif "agent" in t:
        out.append(node("agent", f"{sid}_a", m["agents"][t["agent"]]["name"]))
        base = s["col"] + 1
    else:
        kind = "schedule" if "schedule" in t else "policy"
        out.append(node(kind, f"{sid}_a", t.get("schedule") or t["policy"]))
        base = s["col"] + 1
    if "readmodel" in t:
        out.append(node("readmodel", f"{sid}_r", m["readmodels"][t["readmodel"]]["name"]))
        arrows.append(f"{sid}_r ..> {sid}_a")
    out.append(node("command", f"{sid}_c", s["command"]))
    tg = s["target"]
    if "aggregate" in tg:
        out.append(node("aggregate", f"{sid}_t", m["aggregates"][tg["aggregate"]]["name"]))
    else:
        out.append(node("external", f"{sid}_t", m["externals"][tg["external"]]))
    arrows += [f"{sid}_a --> {sid}_c", f"{sid}_c --> {sid}_t"]
    if s.get("uses"):
        out.append(node("external", f"{sid}_g", m["externals"][s["uses"]]))
        arrows.append(f"{sid}_t .. {sid}_g")
    for e in s["events"]:
        out.append(node("event", e["id"], e["text"]))
        arrows.append(f"{sid}_t --> {e['id']}")
        ev_col[e["id"]] = (base + 2, s["row"] if not e.get("alt") else "alt")
    if "after" in t:
        arrows.append(f"{t['after']} --> {sid}_a")

if TIMELINE:   # порядок во времени для шагов без входящей стрелки: скрытая связь с предыдущим событием
    for s in m["steps"]:
        t = s["trigger"]
        if "after" in t or s["col"] == 0:
            continue
        prev = [(c, e) for e, (c, r) in ev_col.items() if r == s["row"] and c < s["col"]]
        if prev:
            arrows.append(f"{max(prev)[1]} -[hidden]-> {s['id']}_a")

for n, h in enumerate(m["hotspots"]):
    by_ctx[h["ctx"]].append(node("hotspot", f"hot{n}", h["text"]))
    arrows.append(f"hot{n} .. {h['about']}_c")

for c in m["contexts"]:
    if TIMELINE:
        L += by_ctx[c["id"]]
    else:
        L.append(f'rectangle "Ограниченный контекст «{c["name"]}»" as ctx_{c["id"]} <<ctx>> {{')
        L += ["  " + x for x in by_ctx[c["id"]]]
        L.append("}")
L += [""] + arrows + ["@enduml"]
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"{OUT}: {sum(len(v) for v in by_ctx.values())} элементов, {len(arrows)} связей")
