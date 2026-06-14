"""make_excalidraw_diagram.py — generate an editable Excalidraw scene of the
semiconductor production flow.

Writes reports/diagrams/chip_supply_chain.excalidraw — a real Excalidraw file
(schema v2) you can open and edit at https://excalidraw.com (File → Open) and
export to PNG/SVG. Hand-drawn (Virgil) font + sketchy roughness give the native
Excalidraw look.

Run:  python scripts/make_excalidraw_diagram.py
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "reports" / "diagrams" / "chip_supply_chain.excalidraw"
OUT.parent.mkdir(parents=True, exist_ok=True)

_now = lambda: int(time.time() * 1000)
_nonce = lambda: random.randint(1, 2_000_000_000)
elements: list[dict] = []


def _base(kind, x, y, w, h, stroke="#1e1e1e", bg="transparent", **extra):
    e = dict(
        id=f"{kind}-{len(elements)}-{_nonce()}", type=kind,
        x=x, y=y, width=w, height=h, angle=0,
        strokeColor=stroke, backgroundColor=bg, fillStyle="solid",
        strokeWidth=2, strokeStyle="solid", roughness=1, opacity=100,
        groupIds=[], frameId=None, roundness=None, seed=_nonce(),
        version=1, versionNonce=_nonce(), isDeleted=False,
        boundElements=[], updated=_now(), link=None, locked=False,
    )
    e.update(extra)
    return e


def rect(x, y, w, h, stroke, bg="transparent"):
    elements.append(_base("rectangle", x, y, w, h, stroke, bg,
                          roundness={"type": 3}))


def text(x, y, s, size=16, color="#1e1e1e", align="left", w=None):
    lines = s.split("\n")
    w = w or int(max(len(ln) for ln in lines) * size * 0.55)
    h = int(len(lines) * size * 1.25)
    elements.append(_base("text", x, y, w, h, color,
                          text=s, fontSize=size, fontFamily=1,
                          textAlign=align, verticalAlign="top",
                          containerId=None, originalText=s,
                          lineHeight=1.25, autoResize=True,
                          roundness=None))


def line(x, y, pts, stroke="#868e96"):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    elements.append(_base("line", x, y, max(xs) - min(xs) or 1, max(ys) - min(ys) or 1,
                          stroke, points=[[float(a), float(b)] for a, b in pts],
                          lastCommittedPoint=None, startBinding=None, endBinding=None,
                          startArrowhead=None, endArrowhead=None,
                          roundness={"type": 2}))


def arrow(x, y, pts, stroke="#343a40", width=2):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    elements.append(_base("arrow", x, y, max(xs) - min(xs) or 1, max(ys) - min(ys) or 1,
                          stroke, strokeWidth=width,
                          points=[[float(a), float(b)] for a, b in pts],
                          lastCommittedPoint=None, startBinding=None, endBinding=None,
                          startArrowhead=None, endArrowhead="arrow",
                          roundness={"type": 2}))


# --------------------------------------------------------------------------- #
STAGES = [
    ("1 · DIZAJN", "EDA: Synopsys, Cadence\nIP: ARM, SiFive", "US · UK",
     "EDA oligopol (3 firme)", "#6741d9"),
    ("2 · MATERIJALI", "wafer: Shin-Etsu, SUMCO\nrezist: JSR, TOK\nABF: Ajinomoto", "JP · DE",
     "ABF ~100% Ajinomoto", "#f08c00"),
    ("3 · OPREMA", "litografija: ASML\njetkanje/depo:\nAMAT, Lam, TEL", "NL · US · JP",
     "EUV monopol: ASML", "#e8590c"),
    ("4 · LJEVAONICA / IDM", "TSMC, Samsung, Intel\nfront-end fab\n(wafer -> cipovi)", "TW · KR · US",
     "2nm/3nm ~90% TSMC", "#1971c2"),
    ("5 · PAKIRANJE + TEST", "OSAT (back-end)\nASE, Amkor, JCET\nrezanje, kuciste", "TW · US · CN",
     "koncentrirano u Aziji", "#e03131"),
    ("6 · KRAJNJI PROIZVOD", "fabless: Apple,\nNvidia, AMD\nuredaji: Foxconn", "US · TW",
     "ovisnost o Tajvanu", "#2f9e44"),
]

BW, BH, GAP, Y = 220, 160, 55, 270
xs = [40 + i * (BW + GAP) for i in range(len(STAGES))]

# --- title block (clear top band, well above everything) ---
text(40, 24, "Kako nastaje cip: od nacrta do gotovog proizvoda", size=28)
text(40, 74, "Lanac opskrbe poluvodica - glavni koraci, tvrtke, zemlje i uska grla",
     size=15, color="#868e96")
text(40, 106, "Materijali (2) i oprema (3) ulaze u front-end fab (4); "
     "prikazano linearno radi preglednosti.", size=12, color="#adb5bd")

# --- FRONT-END / BACK-END brackets directly above their stage box ---
def bracket(x0, x1, label):
    line(x0, Y - 46, [[0, 16], [0, 0], [x1 - x0, 0], [x1 - x0, 16]], stroke="#adb5bd")
    text(x0, Y - 78, label, size=13, color="#495057")
bracket(xs[3], xs[3] + BW, "FRONT-END (wafer fab)")
bracket(xs[4], xs[4] + BW, "BACK-END (pakiranje)")

# --- stage boxes ---
for x, (title, body, ctry, risk, col) in zip(xs, STAGES):
    rect(x, Y, BW, BH, stroke=col)
    text(x + 14, Y + 14, title, size=17, color=col)
    text(x + 14, Y + 52, body, size=12, color="#1e1e1e")
    text(x + 14, Y + BH - 30, f"[{ctry}]", size=13, color="#343a40")
    text(x + 8, Y + BH + 16, f"! {risk}", size=12, color="#c92a2a")

# --- forward arrows between stages ---
for x in xs[:-1]:
    arrow(x + BW, Y + BH / 2, [[0, 0], [GAP, 0]])

# --- feedback: fabless order production from the foundry (clear bottom band) ---
fb_top = Y + BH + 64
arrow(xs[5] + BW / 2, fb_top,
      [[0, 0], [0, 90], [-(xs[5] - xs[3]), 90], [-(xs[5] - xs[3]), -28]],
      stroke="#1971c2", width=2)
text(xs[3] + 30, fb_top + 104,
     "fabless dizajneri narucuju proizvodnju od ljevaonice", size=13,
     color="#1971c2")

scene = {
    "type": "excalidraw", "version": 2,
    "source": "https://github.com/semiconductor-supply-chain",
    "elements": elements,
    "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
    "files": {},
}
OUT.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {OUT} ({len(elements)} elements)")
