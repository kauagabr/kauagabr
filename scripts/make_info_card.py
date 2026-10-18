#!/usr/bin/env python3
"""Gera info-card.svg — painel estilo `neofetch` que "imprime" linha por linha.

Edite a lista ROWS abaixo para mudar o conteúdo. STATIC=1 gera um quadro congelado.
"""
import os
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER, HOST = "kauagabr", "github"

# (rótulo, valor) — mantenha os valores com até ~42 caracteres para caber na largura
ROWS = [
    ("Agora", "Eng. de Software @ CRIAR e INES.IA"),
    ("Mestrado", "Ciência da Computação (IA) · CIn-UFPE"),
    ("Formação", "Tecnólogo em ADS · IFPE"),
    ("Foco", "IA/ML · Visão Computacional · Saúde"),
    ("Stack", "Python · FastAPI · Django · Deep Learning"),
    ("Pesquisa", "IA na saúde · segmentação de imagens"),
    ("Também", "Testes (BDD) · Dados · Liderança técnica"),
]

W, H = 490, 368  # H casado com a altura do retrato ASCII exibido a 370px
KEY_X, VAL_X = 28, 128
FIRST_Y, STEP = 114, 25
SWATCH = ["#ff5f56", "#ffbd2e", "#27c93f", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9", "#6e7681"]


def main():
    def delay(i):
        return "" if STATIC else f' style="animation-delay:{0.35 + i * 0.22:.2f}s"'

    lines = []
    # cabeçalho user@host + separador
    lines.append(
        f'<g class="ln"{delay(0)}>'
        f'<text x="{KEY_X}" y="72" font-size="15" font-weight="bold">'
        f'<tspan fill="#3fb950">{escape(USER)}</tspan><tspan fill="#c9d1d9">@</tspan>'
        f'<tspan fill="#58a6ff">{escape(HOST)}</tspan></text>'
        f'<text class="dim" x="{KEY_X}" y="92" font-size="13">{"─" * (len(USER) + len(HOST) + 1)}</text></g>'
    )
    # linhas chave: valor
    for i, (k, v) in enumerate(ROWS):
        y = FIRST_Y + i * STEP
        lines.append(
            f'<g class="ln"{delay(i + 1)}>'
            f'<text x="{KEY_X}" y="{y + 12}" font-size="13" font-weight="bold" fill="#58a6ff">{escape(k)}</text>'
            f'<text class="dim" x="{VAL_X - 14}" y="{y + 12}" font-size="13">:</text>'
            f'<text class="fg" x="{VAL_X}" y="{y + 12}" font-size="13">{escape(v)}</text></g>'
        )
    # paleta de cores (assinatura do neofetch)
    sw_y = FIRST_Y + len(ROWS) * STEP + 16
    swatches = "".join(
        f'<rect x="{KEY_X + i * 26}" y="{sw_y}" width="22" height="14" rx="2" fill="{c}"/>'
        for i, c in enumerate(SWATCH)
    )
    lines.append(f'<g class="ln"{delay(len(ROWS) + 1)}>{swatches}</g>')
    # prompt final
    lines.append(
        f'<g class="ln"{delay(len(ROWS) + 2)}>'
        f'<text x="{KEY_X}" y="{H - 28}" font-size="13"><tspan fill="#3fb950">$</tspan>'
        f'<tspan class="fg"> _</tspan></text></g>'
    )

    anim = "" if STATIC else """
.ln{opacity:0;animation:in .45s ease-out forwards}
@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"""

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Resumo de {escape(USER)}: stack, foco e interesses">
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}}
.dim{{fill:#8b949e}}.fg{{fill:#c9d1d9}}{anim}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
<path d="M.5 32V12.5a12 12 0 0 1 12-12h{W - 25}a12 12 0 0 1 12 12V32z" fill="#161b22"/>
<line x1=".5" y1="32.5" x2="{W - .5}" y2="32.5" stroke="#30363d"/>
<circle cx="20" cy="16.5" r="6" fill="#ff5f56"/><circle cx="40" cy="16.5" r="6" fill="#ffbd2e"/><circle cx="60" cy="16.5" r="6" fill="#27c93f"/>
<text class="dim" x="{W / 2}" y="21" font-size="12" text-anchor="middle">{escape(USER)}@{escape(HOST)}: ~</text>
{chr(10).join(lines)}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
