#!/usr/bin/env python3
"""Lê data/contributions.json e desenha contrib-heatmap.svg (animado, toca uma vez).

STATIC=1 gera um quadro congelado (bom para pré-visualizar).
"""
import json
import os
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

W, LEFT, RIGHT, GRID_Y = 860, 46, 24, 68
CELL, GAP = 12, 3


def br(n):
    return f"{n:,}".replace(",", ".")


def plural(n, one, many):
    return f"{br(n)} {one if n == 1 else many}"


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days, stats, user = data["days"], data["stats"], data["username"]

    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)  # domingo da 1ª semana
    ncols = (last - start).days // 7 + 1
    pitch = min(CELL + GAP, (W - LEFT - RIGHT + GAP) / ncols)
    cell = pitch - GAP

    top = max((d["count"] for d in days), default=0)

    def level(d):
        lv = min(d["level"], 4)
        return 5 if (lv == 4 and top and d["count"] >= top * 0.75) else lv

    # --- células ---
    rects = []
    for d in days:
        dt = date.fromisoformat(d["date"])
        col = (dt - start).days // 7
        row = (dt.weekday() + 1) % 7
        x, y = LEFT + col * pitch, GRID_Y + row * pitch
        delay = "" if STATIC else f' style="animation-delay:{0.3 + (col + row) * 0.03:.2f}s"'
        rects.append(
            f'<rect class="c l{level(d)}" x="{x:.1f}" y="{y:.1f}" '
            f'width="{cell:.1f}" height="{cell:.1f}" rx="2.5"{delay}/>'
        )

    # --- rótulos de mês ---
    labels, prev = [], None
    for c in range(ncols):
        m = (start + timedelta(days=7 * c)).month
        if m != prev:
            labels.append((c, m))
            prev = m
    if len(labels) > 1 and labels[1][0] - labels[0][0] < 3:
        labels.pop(0)
    month_txt = "".join(
        f'<text class="dim" x="{LEFT + c * pitch:.1f}" y="{GRID_Y - 10}" font-size="10">{MESES[m - 1]}</text>'
        for c, m in labels
    )
    day_txt = "".join(
        f'<text class="dim" x="{LEFT - 10}" y="{GRID_Y + r * pitch + cell - 2:.1f}" '
        f'font-size="10" text-anchor="end">{n}</text>'
        for r, n in ((1, "seg"), (3, "qua"), (5, "sex"))
    )

    # --- rodapé ---
    grid_end = GRID_Y + 7 * pitch - GAP
    y1, y2 = grid_end + 30, grid_end + 50
    H = int(y2 + 22)

    best = stats["best_day"]
    bd = date.fromisoformat(best["date"]).strftime("%d/%m/%Y")
    line1 = f'{br(stats["total"])} contribuições no último ano'
    line2 = (
        f'sequência atual: {plural(stats["current_streak"], "dia", "dias")}  ·  '
        f'maior sequência: {plural(stats["longest_streak"], "dia", "dias")}  ·  '
        f'melhor dia: {br(best["count"])} em {bd}'
    )

    # legenda (alinhada à direita)
    xr = W - RIGHT
    sq, sg = 10, 3
    legend_w = 6 * sq + 5 * sg
    sx = xr - 26 - 6 - legend_w
    legend = (
        f'<text class="dim t" x="{sx - 6}" y="{y1}" font-size="11" text-anchor="end">menos</text>'
        + "".join(
            f'<rect class="l{i}" x="{sx + i * (sq + sg)}" y="{y1 - 9:.1f}" width="{sq}" height="{sq}" rx="2"/>'
            for i in range(6)
        )
        + f'<text class="dim t" x="{xr}" y="{y1}" font-size="11" text-anchor="end">mais</text>'
    )

    anim = "" if STATIC else """
.c{opacity:0;animation:drop .5s ease-out forwards}
@keyframes drop{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}
.t{opacity:0;animation:fade .6s ease-out 2s forwards}
@keyframes fade{from{opacity:0}to{opacity:1}}"""
    levels_css = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(PALETTE))

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Gráfico de contribuições de {escape(user)} no GitHub">
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}}
.dim{{fill:#8b949e}}.fg{{fill:#c9d1d9}}
{levels_css}{anim}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
<path d="M.5 32V12.5a12 12 0 0 1 12-12h{W - 25}a12 12 0 0 1 12 12V32z" fill="#161b22"/>
<line x1=".5" y1="32.5" x2="{W - .5}" y2="32.5" stroke="#30363d"/>
<circle cx="20" cy="16.5" r="6" fill="#ff5f56"/><circle cx="40" cy="16.5" r="6" fill="#ffbd2e"/><circle cx="60" cy="16.5" r="6" fill="#27c93f"/>
<text class="dim" x="{W / 2}" y="21" font-size="12" text-anchor="middle">{escape(user)}@github: ~/contribuições</text>
{month_txt}{day_txt}
{chr(10).join(rects)}
<text class="fg t" x="{LEFT}" y="{y1}" font-size="12" font-weight="bold">{escape(line1)}</text>
<text class="dim t" x="{LEFT}" y="{y2}" font-size="11">{escape(line2)}</text>
{legend}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"→ {OUT} ({len(svg) // 1024} KB, {len(rects)} células)")


if __name__ == "__main__":
    main()
