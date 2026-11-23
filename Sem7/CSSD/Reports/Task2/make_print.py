"""(Адаптировано: работает на Windows, Linux, macOS.)
Лист 1 .drawio -> PDF для печати: обзор с легендой и фрагменты ленты на A3 книжной ориентации.

Фрагменты режутся по промежуткам между столбцами, поэтому стикеры не разрезаются.
На каждый фрагмент повторяются названия дорожек-контекстов.
"""
import json
import os
import shutil
import subprocess
import sys

import yaml
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None          # лента большая, иначе Pillow принимает её за «бомбу»
DRAWIO, OUT = "ES_replays.drawio", "ES_replays_печать_A3.pdf"
TITLE = yaml.safe_load(open("model.yaml", encoding="utf-8"))["title"]
COLS_PER_SHEET = int(sys.argv[1]) if len(sys.argv) > 1 else 7
L = json.load(open("layout.json"))


def find_drawio():
    for c in (shutil.which("drawio"), shutil.which("draw.io"),
              r"C:\Program Files\draw.io\draw.io.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Programs\draw.io\draw.io.exe"),
              "/Applications/draw.io.app/Contents/MacOS/draw.io"):
        if c and os.path.exists(c):
            return c
    sys.exit("Не найден draw.io Desktop: установите его или впишите путь в find_drawio()")


# Векторный PDF из draw.io, затем растр. xvfb-run нужен только на Linux без экрана.
cmd = [find_drawio(), "-x", "-f", "pdf", "-p", "1", "-b", "0", "--crop", "-o", "_map.pdf", DRAWIO]
if sys.platform.startswith("linux"):
    cmd.insert(1, "--no-sandbox")
    if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a"] + cmd
subprocess.run(cmd, check=True)
if shutil.which("pdftoppm"):
    subprocess.run(["pdftoppm", "-png", "-r", "200", "-singlefile", "_map.pdf", "_full"], check=True)
else:                                   # Windows: вместо poppler берём PyMuPDF (pip install pymupdf)
    import fitz
    fitz.open("_map.pdf")[0].get_pixmap(dpi=200).save("_full.png")
full = Image.open("_full.png").convert("RGB")
g = full.convert("L").point(lambda v: 255 if v < 200 else 0)
left, top_, right, bottom = g.getbbox()
X_RIGHT = L["MAP_W"] - 10                       # правый край дорожек
Y_BOTTOM = L["MAP_H"] - 30 - 16                 # нижний край последней дорожки
S = (right - left) / (X_RIGHT - L["X0"])
px = lambda x: int(round(left + (x - L["X0"]) * S))
py = lambda y: int(round(bottom - (Y_BOTTOM - y) * S))
print(f"растр {full.size}, масштаб {S:.3f} пикселя на пиксель холста")

DPI = 200
A3P = (int(297 / 25.4 * DPI), int(420 / 25.4 * DPI))
A3L = (A3P[1], A3P[0])
MARGIN = int(10 / 25.4 * DPI)
def font_path(*names):
    for d in ("/usr/share/fonts/truetype/dejavu", r"C:\Windows\Fonts", "/Library/Fonts", "/System/Library/Fonts/Supplemental"):
        for n in names:
            if os.path.exists(os.path.join(d, n)):
                return os.path.join(d, n)
    sys.exit("Не найден шрифт с кириллицей")
F = font_path("DejaVuSans.ttf", "arial.ttf", "Arial.ttf")
FB = font_path("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf")
f_head, f_small = ImageFont.truetype(FB, 34), ImageFont.truetype(F, 26)

y_top, y_bot = py(L["Y_LANES"] - 4), py(Y_BOTTOM + 4)
hdr = full.crop((0, y_top, px(L["X0"] + L["HDR"]) + 2, y_bot))
col_x = lambda k: L["X0"] + L["HDR"] + k * L["PITCH"]
n_sheets = -(-L["MAX_COL"] // COLS_PER_SHEET)

def fit(img, box_w, box_h):
    k = min(box_w / img.width, box_h / img.height)
    return img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS), k

pages, frames = [], []
for i in range(n_sheets):
    a, b = i * COLS_PER_SHEET, min((i + 1) * COLS_PER_SHEET, L["MAX_COL"])
    x1, x2 = px(col_x(a)), px(col_x(b))
    frames.append((x1, x2))
    body = full.crop((x1, y_top, x2, y_bot))
    tile = Image.new("RGB", (hdr.width + body.width, body.height), "white")
    tile.paste(hdr, (0, 0)); tile.paste(body, (hdr.width, 0))
    page = Image.new("RGB", A3P, "white")
    d = ImageDraw.Draw(page)
    title = f"{TITLE}. Лист {i + 2} из {n_sheets + 1}, столбцы с {a + 1} по {b}"
    d.text((MARGIN, MARGIN), title, font=f_head, fill="black")
    img, k = fit(tile, A3P[0] - 2 * MARGIN, A3P[1] - 2 * MARGIN - 110)
    page.paste(img, (MARGIN, MARGIN + 60))
    if i + 1 < n_sheets:
        d.text((MARGIN, A3P[1] - MARGIN - 34), f"Продолжение ленты на листе {i + 3}", font=f_small, fill="black")
    pages.append(page)
    mm_per_px = (img.width / tile.width) * (25.4 / DPI) * S   # мм на пиксель исходного холста
    if i == 0:
        print(f"масштаб: {mm_per_px:.3f} мм на пиксель холста; текст 13 px = {13 * mm_per_px / 0.3528:.1f} пт, "
              f"подпись типа 11 px = {11 * mm_per_px / 0.3528:.1f} пт")

# обзорный лист: легенда крупно, под ней вся лента с рамками фрагментов
ov = Image.new("RGB", A3L, "white")
d = ImageDraw.Draw(ov)
d.text((MARGIN, MARGIN), f"{TITLE}. Лист 1: легенда и схема листов", font=f_head, fill="black")
legend = full.crop((0, py(60), px(L["X0"] + 2700), py(L["Y_LANES"] - 60)))
lg, _ = fit(legend, A3L[0] - 2 * MARGIN, 700)
ov.paste(lg, (MARGIN, MARGIN + 70))
lane_img = full.crop((0, y_top, full.width, y_bot)).copy()
dl = ImageDraw.Draw(lane_img)
f_num = ImageFont.truetype(FB, 150)
for j, (x1, x2) in enumerate(frames):
    dl.rectangle((x1, 0, x2 - 1, lane_img.height - 1), outline="black", width=10)
    dl.text((x1 + 30, 20), str(j + 2), font=f_num, fill="black")
top = MARGIN + 90 + lg.height
lm, _ = fit(lane_img, A3L[0] - 2 * MARGIN, A3L[1] - top - MARGIN)
ov.paste(lm, (MARGIN, top))
ov.save(OUT, "PDF", resolution=DPI, save_all=True, append_images=pages)
print(f"{OUT}: {len(pages) + 1} листов A3")
