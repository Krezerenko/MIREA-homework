"""model.yaml -> ES_velo.drawio: лист 1 карта событий, лист 2 агрегаты, лист 3 контексты.

Проверки при сборке: ссылки модели, занятость ячеек раскладки,
прохождение стрелок сквозь стикеры. При ошибке файл не пишется.
"""
import json
import sys
from xml.sax.saxutils import escape, quoteattr

import yaml

SRC = sys.argv[1] if len(sys.argv) > 1 else "model.yaml"
OUT = sys.argv[2] if len(sys.argv) > 2 else "ES_velo.drawio"
m = yaml.safe_load(open(SRC, encoding="utf-8"))

# Нотация: цвет по Таблице 1, подпись типа, плюс форма и рамка для чёрно-белой печати
KIND = {
    "event":     dict(cap="событие",          fill="#FFA940", w=128, h=112, st="rounded=0;"),
    "command":   dict(cap="команда",          fill="#69B1FF", w=128, h=112, st="rounded=0;strokeWidth=3;"),
    "actor":     dict(cap="участник",         fill="#FFF566", w=112, h=58,  st="rounded=0;"),
    "agent":     dict(cap="ИИ-агент",         fill="#87E8DE", w=112, h=72,  st="rounded=1;arcSize=30;dashed=1;dashPattern=1 3;strokeWidth=2;"),
    "aggregate": dict(cap="агрегат",          fill="#FFE58F", w=140, h=140, st="rounded=0;strokeWidth=2;"),
    "policy":    dict(cap="политика",         fill="#D3ADF7", w=130, h=124, st="rounded=0;dashed=1;dashPattern=6 3;strokeWidth=1.5;"),
    "schedule":  dict(cap="политика, по расписанию", fill="#D3ADF7", w=130, h=124,
                      st="rounded=0;dashed=1;dashPattern=6 3;strokeWidth=1.5;"),
    "external":  dict(cap="внешняя система",  fill="#FFADD2", w=132, h=82,  st="shape=process;backgroundOutline=1;size=0.08;"),
    "readmodel": dict(cap="модель чтения",    fill="#95DE64", w=128, h=82,  st="shape=document;size=0.18;boundedLbl=1;"),
    "hotspot":   dict(cap="горячая точка",    fill="#FF7875", w=150, h=118, st="shape=hexagon;perimeter=hexagonPerimeter2;size=0.07;fixedSize=0;spacingLeft=10;spacingRight=10;"),
}
ROW_H = {"top": 132, "actor": 88, "main": 162, "actor2": 132, "branch": 162, "branch2": 162}
ALT = {"main": "branch", "branch": "branch2"}
UP = {"main": "actor", "branch": "actor2"}
X0, PITCH, HDR, GAP, Y_LANES = 40, 160, 46, 16, 300
FONT = "fontFamily=Arial;fontColor=#000000;"

errors = []

# ---------------------------------------------------------------- проверка ссылок
def check_refs():
    for k in m:
        if not isinstance(k, str):
            errors.append(f"ключ верхнего уровня {k!r} прочитан YAML не как строка")
    ids, ev = set(), {}
    for s in m["steps"]:
        if s["id"] in ids:
            errors.append(f"повтор id шага {s['id']}")
        ids.add(s["id"])
        for k in list(s) + list(s["trigger"]) + list(s["target"]):
            if not isinstance(k, str):
                errors.append(f"шаг {s['id']}: ключ {k!r} не строка (ловушка YAML 1.1)")
        for e in s["events"]:
            if e["id"] in ev:
                errors.append(f"повтор id события {e['id']}")
            ev[e["id"]] = s["id"]
    for s in m["steps"]:
        t = s["trigger"]
        if "after" in t and t["after"] not in ev:
            errors.append(f"{s['id']}: нет события {t['after']}")
        for key, pool in (("actor", "actors"), ("agent", "agents"), ("readmodel", "readmodels")):
            if key in t and t[key] not in m[pool]:
                errors.append(f"{s['id']}: нет {key} {t[key]}")
        tg = s["target"]
        if "aggregate" in tg and tg["aggregate"] not in m["aggregates"]:
            errors.append(f"{s['id']}: нет агрегата {tg['aggregate']}")
        if "external" in tg and tg["external"] not in m["externals"]:
            errors.append(f"{s['id']}: нет внешней системы {tg['external']}")
        if s.get("uses") and s["uses"] not in m["externals"]:
            errors.append(f"{s['id']}: нет внешней системы {s['uses']}")
    for h in m["hotspots"]:
        if h["about"] not in ids:
            errors.append(f"горячая точка ссылается на неизвестный шаг {h['about']}")
    for r in m["readmodels"].values():
        for e in r["from"]:
            if e not in ev:
                errors.append(f"модель чтения {r['name']}: нет события {e}")
    return ev

ev_step = check_refs()

# ---------------------------------------------------------------- раскладка листа 1
row_cy, lane_box = {}, {}
y = Y_LANES
for c in m["contexts"]:
    top = y
    for r in c["rows"]:
        row_cy[(c["id"], r)] = y + ROW_H[r] / 2
        y += ROW_H[r]
    lane_box[c["id"]] = (top, y)
    y += GAP
MAP_H = y + 30

def cx(col):
    return X0 + HDR + col * PITCH + PITCH / 2

slots = {}      # (ctx,row,col) -> описание, для проверки наложений
cells1, edges1, pos, label_of = [], [], {}, {}
nid = [0]

def new_id(p):
    nid[0] += 1
    return f"{p}{nid[0]}"

def html(cap, text, big=False):
    fs = 14 if big else 13
    return (f'<div style="font-size:11px;font-style:italic;margin-bottom:3px">{escape(cap)}</div>'
            f'<div style="font-size:{fs}px">{escape(text)}</div>')

def sticky(kind, text, x_c, y_c, out, slot=None, big=False):
    k = KIND[kind]
    if slot:
        if slot in slots:
            errors.append(f"наложение в ячейке {slot}: «{slots[slot]}» и «{text}»")
        slots[slot] = text
    i = new_id("n")
    style = (f"whiteSpace=wrap;html=1;fillColor={k['fill']};strokeColor=#1F1F1F;{FONT}"
             f"verticalAlign=middle;spacing=4;{k['st']}")
    pos[i] = (x_c, y_c, k["w"], k["h"])
    label_of[i] = text
    out.append(f'<mxCell id="{i}" value={quoteattr(html(k["cap"], text, big))} style="{style}" '
               f'vertex="1" parent="1"><mxGeometry x="{x_c - k["w"]/2:.0f}" y="{y_c - k["h"]/2:.0f}" '
               f'width="{k["w"]}" height="{k["h"]}" as="geometry"/></mxCell>')
    return i

PORT_OUT = {"right": (1, .5), "bottom": (.5, 1), "top": (.5, 0)}
PORT_IN = {"left": (0, .5), "top": (.5, 0), "bottom": (.5, 1)}
routes = []     # (edge_id, [точки пути]) для проверки пересечений

def edge(out, a, b, o="right", n="left", pts=None, dashed=False, arrow=True, label=""):
    i = new_id("e")
    ex, ey = PORT_OUT[o]
    nx, ny = PORT_IN[n]
    st = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#333333;strokeWidth=1.3;{FONT}"
          f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;"
          + ("dashed=1;" if dashed else "")
          + ("endArrow=block;endFill=1;" if arrow else "endArrow=none;"))
    geo = ""
    if pts:
        geo = '<Array as="points">' + "".join(f'<mxPoint x="{px:.0f}" y="{py:.0f}"/>' for px, py in pts) + "</Array>"
    out.append(f'<mxCell id="{i}" value={quoteattr(label)} style="{st}" edge="1" parent="1" '
               f'source="{a}" target="{b}"><mxGeometry relative="1" as="geometry">{geo}</mxGeometry></mxCell>')
    if a in pos and b in pos:
        (ax, ay, aw, ah), (bx, by, bw, bh) = pos[a], pos[b]
        p0 = (ax - aw/2 + ex*aw, ay - ah/2 + ey*ah)
        p1 = (bx - bw/2 + nx*bw, by - bh/2 + ny*bh)
        routes.append((a, b, [p0] + (pts or []) + [p1]))
    return i

# ---- дорожки контекстов
MAX_COL = max(max(s["col"] + 4 for s in m["steps"]), max(h["col"] for h in m["hotspots"])) + 1
MAP_W = X0 + HDR + MAX_COL * PITCH + 30
lanes = []
for c in m["contexts"]:
    t, b = lane_box[c["id"]]
    st = (f"swimlane;horizontal=0;startSize={HDR};container=0;collapsible=0;html=1;{FONT}fontSize=16;"
          "fontStyle=1;fillColor=#EDEDED;swimlaneFillColor=#FAFAFA;strokeColor=#404040;"
          "dashed=1;dashPattern=10 5;strokeWidth=2;")
    lanes.append(f'<mxCell id="{new_id("lane")}" value={quoteattr("Ограниченный контекст «" + c["name"] + "»")} '
                 f'style="{st}" vertex="1" parent="1"><mxGeometry x="{X0}" y="{t}" '
                 f'width="{MAP_W - X0 - 10}" height="{b - t}" as="geometry"/></mxCell>')

# ---- шаги
ev_cell, trig_cell = {}, {}
for s in m["steps"]:
    ctx, row, col, t = s["ctx"], s["row"], s["col"], s["trigger"]
    y_row = row_cy[(ctx, row)]
    if "actor" in t:
        up = UP[row]
        a = sticky("actor", m["actors"][t["actor"]], cx(col), row_cy[(ctx, up)], cells1, (ctx, up, col))
        c_cmd, a_o, a_n = col, "bottom", "top"
        if "readmodel" in t:
            r = sticky("readmodel", m["readmodels"][t["readmodel"]]["name"], cx(col - 1),
                       row_cy[(ctx, up)], cells1, (ctx, up, col - 1))
            edge(edges1, r, a, "right", "left", dashed=True)
    elif "agent" in t:
        a = sticky("agent", m["agents"][t["agent"]]["name"], cx(col), y_row, cells1, (ctx, row, col))
        c_cmd, a_o, a_n = col + 1, "right", "left"
        if "readmodel" in t:
            up = UP[row]
            r = sticky("readmodel", m["readmodels"][t["readmodel"]]["name"], cx(col),
                       row_cy[(ctx, up)], cells1, (ctx, up, col))
            edge(edges1, r, a, "bottom", "top", dashed=True)
    else:
        kind = "schedule" if "schedule" in t else "policy"
        a = sticky(kind, t.get("schedule") or t["policy"], cx(col), y_row, cells1, (ctx, row, col))
        c_cmd, a_o, a_n = col + 1, "right", "left"
    trig_cell[s["id"]] = a
    cmd = sticky("command", s["command"], cx(c_cmd), y_row, cells1, (ctx, row, c_cmd))
    edge(edges1, a, cmd, a_o, a_n)
    tg = s["target"]
    if "aggregate" in tg:
        tc = sticky("aggregate", m["aggregates"][tg["aggregate"]]["name"], cx(c_cmd + 1), y_row,
                    cells1, (ctx, row, c_cmd + 1), big=True)
    else:
        tc = sticky("external", m["externals"][tg["external"]], cx(c_cmd + 1), y_row,
                    cells1, (ctx, row, c_cmd + 1))
    edge(edges1, cmd, tc)
    if s.get("uses"):
        g = sticky("external", m["externals"][s["uses"]], cx(c_cmd + 1), row_cy[(ctx, "top")],
                   cells1, (ctx, "top", c_cmd + 1))
        edge(edges1, tc, g, "top", "bottom", dashed=True, arrow=False)
    for e in s["events"]:
        r = ALT[row] if e.get("alt") else row
        ec = sticky("event", e["text"], cx(c_cmd + 2), row_cy[(ctx, r)], cells1, (ctx, r, c_cmd + 2))
        ev_cell[e["id"]] = ec
        if e.get("alt"):
            edge(edges1, tc, ec, "bottom", "left", pts=[(cx(c_cmd + 1), row_cy[(ctx, r)])])
        else:
            edge(edges1, tc, ec)

# связи событие -> политика или ИИ-агент; межстрочные прокладываются явно
for s in m["steps"]:
    t = s["trigger"]
    if "after" not in t:
        continue
    src, dst = ev_cell[t["after"]], trig_cell[s["id"]]
    (ax, ay, aw, _), (bx, by, bw, _) = pos[src], pos[dst]
    if abs(ay - by) < 1:
        edge(edges1, src, dst)
    else:
        if "route_gap" in t:           # явный канал: промежуток справа от столбца route_gap
            xv = cx(t["route_gap"]) + PITCH / 2 + t.get("route_dx", 0)
        else:
            xv = ((ax + aw/2) + (bx - bw/2)) / 2 + t.get("route_dx", 0)
        edge(edges1, src, dst, pts=[(xv, ay), (xv, by)])

for h in m["hotspots"]:
    sticky("hotspot", h["text"], cx(h["col"]), row_cy[(h["ctx"], h["row"])], cells1, (h["ctx"], h["row"], h["col"]))

# ---- проверка: стрелка не должна проходить сквозь чужой стикер
def seg_hits(p, q, box, pad=3):
    x, y_, w, h = box
    l, r, t_, b = x - w/2 - pad, x + w/2 + pad, y_ - h/2 - pad, y_ + h/2 + pad
    if abs(p[0] - q[0]) < 0.5:                       # вертикальный отрезок
        y1, y2 = sorted((p[1], q[1]))
        return l < p[0] < r and y1 < b and y2 > t_
    x1, x2 = sorted((p[0], q[0]))                    # горизонтальный
    return t_ < p[1] < b and x1 < r and x2 > l

for a, b, path in routes:
    for p, q in zip(path, path[1:]):
        for cid, box in pos.items():
            if cid in (a, b):
                continue
            if seg_hits(p, q, box):
                errors.append(f"стрелка «{label_of[a]}» → «{label_of[b]}» проходит сквозь «{label_of[cid]}»")

# ---- заголовок и легенда
head = []
head.append(f'<mxCell id="{new_id("t")}" value={quoteattr(m["title"])} style="text;html=1;{FONT}fontSize=26;'
            f'fontStyle=1;align=left;verticalAlign=middle;" vertex="1" parent="1">'
            f'<mxGeometry x="{X0}" y="20" width="1200" height="40" as="geometry"/></mxCell>')
LEG = [("event", "прошедшее время"), ("command", "неопределённая форма глагола"),
       ("actor", "роль стейкхолдера"), ("agent", "название агента по задаче"),
       ("aggregate", "существительное, ед. ч."), ("policy", "когда ..., то ..."),
       ("schedule", "по расписанию ..."), ("external", "название системы"),
       ("readmodel", "название набора данных"), ("hotspot", "вопрос?")]
lx = X0
for kind, rule in LEG:
    k = KIND[kind]
    i = new_id("lg")
    style = f"whiteSpace=wrap;html=1;fillColor={k['fill']};strokeColor=#1F1F1F;{FONT}{k['st']}"
    head.append(f'<mxCell id="{i}" value={quoteattr(html(k["cap"], rule))} style="{style}" vertex="1" '
                f'parent="1"><mxGeometry x="{lx}" y="{80 + (138 - k["h"]) / 2:.0f}" width="{k["w"]}" '
                f'height="{k["h"]}" as="geometry"/></mxCell>')
    lx += k["w"] + 18
bnd = ("whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#404040;dashed=1;dashPattern=10 5;"
       f"strokeWidth=2;{FONT}")
head.append(f'<mxCell id="{new_id("lg")}" value={quoteattr(html("граница контекста", "дорожка с названием контекста"))} '
            f'style="{bnd}" vertex="1" parent="1"><mxGeometry x="{lx}" y="95" width="150" height="106" as="geometry"/></mxCell>')
note = ("Стрелки: участник, ИИ-агент или политика → команда → агрегат или внешняя система → событие → "
        "политика или ИИ-агент. Пунктир со стрелкой: модель чтения, по которой принимается решение. "
        "Пунктир без стрелки: обмен агрегата с внешней системой.")
head.append(f'<mxCell id="{new_id("t")}" value={quoteattr(note)} style="text;html=1;{FONT}fontSize=14;'
            f'align=left;verticalAlign=top;whiteSpace=wrap;" vertex="1" parent="1">'
            f'<mxGeometry x="{lx + 175}" y="92" width="560" height="110" as="geometry"/></mxCell>')

# ================================================================ лист 2: агрегаты
cells2 = []
ctx_name = {c["id"]: c["name"] for c in m["contexts"]}
by_agg = {k: {"cmd": [], "ev": []} for k in m["aggregates"]}
for s in m["steps"]:
    tg = s["target"].get("aggregate")
    if tg:
        if s["command"] not in by_agg[tg]["cmd"]:
            by_agg[tg]["cmd"].append(s["command"])
        by_agg[tg]["ev"] += [e["text"] for e in s["events"]]
yy = 90
cells2.append(f'<mxCell id="{new_id("t")}" value="Агрегаты: команды, события, инварианты" style="text;html=1;'
              f'{FONT}fontSize=24;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="40" y="20" '
              f'width="900" height="40" as="geometry"/></mxCell>')
AGG_W = 1480
for key, a in m["aggregates"].items():
    ncmd, nev = len(by_agg[key]["cmd"]), len(by_agg[key]["ev"])
    ncol = max(ncmd, nev)
    card_h = 2 * 118 + 60
    cells2.append(f'<mxCell id="{new_id("c")}" value="" style="rounded=0;html=1;fillColor=#FAFAFA;strokeColor=#808080;" '
                  f'vertex="1" parent="1"><mxGeometry x="30" y="{yy - 10}" width="{AGG_W}" height="{card_h}" as="geometry"/></mxCell>')
    sticky("aggregate", a["name"], 40 + 75, yy + 118, cells2, big=True)
    cells2.append(f'<mxCell id="{new_id("t")}" value={quoteattr("контекст «" + ctx_name[a["ctx"]] + "»")} '
                  f'style="text;html=1;{FONT}fontSize=12;fontStyle=2;align=center;" vertex="1" parent="1">'
                  f'<mxGeometry x="40" y="{yy + 195}" width="150" height="24" as="geometry"/></mxCell>')
    for j, c_ in enumerate(by_agg[key]["cmd"]):
        sticky("command", c_, 230 + j * 132 + 61, yy + 55, cells2)
    for j, e_ in enumerate(by_agg[key]["ev"]):
        sticky("event", e_, 230 + j * 132 + 61, yy + 175, cells2)
    inv = "<b>Инварианты</b><br>" + "<br>".join("• " + escape(x) for x in a["invariants"])
    cells2.append(f'<mxCell id="{new_id("t")}" value={quoteattr(inv)} style="text;html=1;{FONT}fontSize=14;'
                  f'align=left;verticalAlign=top;whiteSpace=wrap;spacing=8;fillColor=#FFFFFF;strokeColor=#BFBFBF;" '
                  f'vertex="1" parent="1"><mxGeometry x="{230 + 6 * 132 + 20}" y="{yy}" width="{AGG_W - (230 + 6*132 + 20) + 20}" '
                  f'height="{card_h - 20}" as="geometry"/></mxCell>')
    if ncol > 6:
        errors.append(f"агрегат {a['name']}: больше 6 команд или событий, карточка не вмещает")
    yy += card_h + 24
PAGE2_H = yy + 20

# ================================================================ лист 3: контексты
cells3 = []
cells3.append(f'<mxCell id="{new_id("t")}" value="Границы ограниченных контекстов" style="text;html=1;{FONT}'
              f'fontSize=24;fontStyle=1;align=left;" vertex="1" parent="1"><mxGeometry x="40" y="20" width="900" '
              f'height="40" as="geometry"/></mxCell>')
order = ["pay", "rent", "st"]
BW, BY, BH, BGAP = 420, 110, 640, 330
BX = {c: 40 + i * (BW + BGAP) for i, c in enumerate(order)}
for c in order:
    cells3.append(f'<mxCell id="{new_id("cx")}" value={quoteattr("Контекст «" + ctx_name[c] + "»")} style="rounded=1;arcSize=3;html=1;'
                  f'{FONT}fontSize=18;fontStyle=1;verticalAlign=top;dashed=1;dashPattern=10 5;strokeWidth=2;'
                  f'fillColor=#FAFAFA;strokeColor=#404040;" vertex="1" parent="1"><mxGeometry x="{BX[c]}" '
                  f'y="{BY}" width="{BW}" height="{BH}" as="geometry"/></mxCell>')
    aggs = [a["name"] for a in m["aggregates"].values() if a["ctx"] == c]
    for j, n in enumerate(aggs):
        sticky("aggregate", n, BX[c] + 110 + j * 200, BY + 135, cells3, big=True)
    in_ctx = [s for s in m["steps"] if s["ctx"] == c]
    left = sorted({m["actors"][s["trigger"]["actor"]] for s in in_ctx if "actor" in s["trigger"]})
    agents_ = sorted({m["agents"][s["trigger"]["agent"]]["name"] for s in in_ctx if "agent" in s["trigger"]})
    right = sorted({m["externals"][s["uses"]] for s in in_ctx if s.get("uses")} |
                   {m["externals"][s["target"]["external"]] for s in in_ctx if "external" in s["target"]})
    y3 = BY + 290
    for n in left:
        sticky("actor", n, BX[c] + 110, y3, cells3); y3 += 90
    for n in agents_:
        sticky("agent", n, BX[c] + 110, y3, cells3); y3 += 100
    y3 = BY + 290
    for n in right:
        sticky("external", n, BX[c] + 310, y3, cells3); y3 += 110
# межконтекстные связи: какие события вызывают реакцию в другом контексте
flows = {}
step_ctx = {s["id"]: s["ctx"] for s in m["steps"]}
ev_text = {e["id"]: e["text"] for s in m["steps"] for e in s["events"]}
for s in m["steps"]:
    t = s["trigger"]
    if "after" in t:
        a_, b_ = step_ctx[ev_step[t["after"]]], s["ctx"]
        if a_ != b_:
            flows.setdefault((a_, b_), []).append(ev_text[t["after"]])
ARROW = f"html=1;{FONT}fontSize=13;strokeWidth=1.6;endArrow=block;endFill=1;labelBackgroundColor=#FFFFFF;"
def flow_edge(lab, pts_xy):
    (x1, y1), (x2, y2) = pts_xy[0], pts_xy[-1]
    mid = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in pts_xy[1:-1])
    cells3.append(f'<mxCell id="{new_id("f")}" value={quoteattr(lab)} style="{ARROW}{"edgeStyle=orthogonalEdgeStyle;" if mid else ""}" '
                  f'edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/>'
                  f'<mxPoint x="{x2}" y="{y2}" as="targetPoint"/>{"<Array as=%spoints%s>" % (chr(34), chr(34)) + mid + "</Array>" if mid else ""}'
                  f'</mxGeometry></mxCell>')
for (a_, b_), evs in sorted(flows.items()):
    lab = "<br>".join("«" + escape(x) + "»" for x in evs)
    ia, ib = order.index(a_), order.index(b_)
    if abs(ia - ib) == 1:
        y_ = BY + (250 if ia < ib else 470)
        xa = BX[a_] + (BW if ia < ib else 0)
        xb = BX[b_] + (0 if ia < ib else BW)
        flow_edge(lab, [(xa, y_), (xb, y_)])
    else:                                   # в обход среднего контекста снизу
        off = 60 if ia < ib else 140
        xa, xb = BX[a_] + BW / 2 + (-50 if ia < ib else 50), BX[b_] + BW / 2 + (-50 if ia < ib else 50)
        flow_edge(lab, [(xa, BY + BH), (xa, BY + BH + off), (xb, BY + BH + off), (xb, BY + BH)])
# обоснование линий раздела и термины
txt = []
for b_ in m["boundaries"]:
    if b_.get("kind") == "not_a_boundary":
        n1, n2 = (m["aggregates"][x]["name"] for x in b_["between"])
        txt.append(f"<b>Почему между агрегатами «{n1}» и «{n2}» нет границы.</b> {escape(b_['reason'])}")
    else:
        n1, n2 = (ctx_name[x] for x in b_["between"])
        txt.append(f"<b>Граница «{n1}» и «{n2}».</b> {escape(b_['reason'])}")
for t_ in m["terms"]:
    parts = "; ".join(f"в контексте «{ctx_name[c]}» это {escape(v[0].lower() + v[1:])}" for c, v in t_["meanings"].items())
    txt.append(f"<b>Термин «{escape(t_['term'])}»:</b> {parts}.")
cells3.append(f'<mxCell id="{new_id("t")}" value={quoteattr("<br><br>".join(txt))} style="text;html=1;{FONT}fontSize=15;'
              f'align=left;verticalAlign=top;whiteSpace=wrap;spacing=10;fillColor=#FFFFFF;strokeColor=#BFBFBF;" '
              f'vertex="1" parent="1"><mxGeometry x="40" y="{BY + BH + 190}" width="{3 * BW + 2 * BGAP}" height="230" as="geometry"/></mxCell>')
PAGE3_H = BY + BH + 460

# ================================================================ запись
if errors:
    print("ОШИБКИ СБОРКИ:")
    for e in errors:
        print("  -", e)
    sys.exit(1)

def page(pid, name, body, w, h):
    return (f'<diagram id="{pid}" name={quoteattr(name)}><mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" '
            f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            f'pageWidth="{w:.0f}" pageHeight="{h:.0f}" math="0" shadow="0"><root><mxCell id="0"/>'
            f'<mxCell id="1" parent="0"/>{"".join(body)}</root></mxGraphModel></diagram>')

xml = ('<mxfile host="generator" type="device">'
       + page("map", "Карта событий", lanes + head + cells1 + edges1, MAP_W, MAP_H)
       + page("aggs", "Агрегаты", cells2, AGG_W + 60, PAGE2_H)
       + page("ctx", "Контексты", cells3, 3 * BW + 2 * BGAP + 80, PAGE3_H)
       + "</mxfile>")
open(OUT, "w", encoding="utf-8").write(xml)
# геометрия столбцов для нарезки листов печати
json.dump({"X0": X0, "HDR": HDR, "PITCH": PITCH, "MAX_COL": MAX_COL, "MAP_W": MAP_W, "MAP_H": MAP_H,
           "Y_LANES": Y_LANES}, open("layout.json", "w"))
print(f"{OUT}: карта {len(cells1)} элементов и {len(edges1)} связей, холст {MAP_W:.0f}x{MAP_H:.0f}; "
      f"проверки пройдены (ячеек {len(slots)}, маршрутов {len(routes)})")
