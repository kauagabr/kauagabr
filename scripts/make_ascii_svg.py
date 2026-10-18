#!/usr/bin/env python3
"""Converte source-prepped.png em ascii-portrait.svg (monocromático, "digita" linha a linha).
Polaridade: pixel claro = caractere denso (tinta clara sobre cartão escuro).

Sem foto preparada, gera um placeholder com as iniciais — assim o layout já funciona
antes de você escolher a sua foto. STATIC=1 gera um quadro congelado.

Uso:  python scripts/make_ascii_svg.py            # usa source-prepped.png (ou placeholder)
      python scripts/make_ascii_svg.py --text KG  # força o placeholder com outras iniciais
"""
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "ascii-portrait.svg"
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"  # escuro (esparso) -> claro (denso). Tinta clara sobre cartão escuro:
# o fundo preto vira espaço e as áreas iluminadas (rosto) viram caracteres densos
COLS, ROWS = 100, 53
CW, LH, FS = 4.8, 9.0, 8  # largura do caractere, altura da linha, tamanho da fonte
PAD = 12
INK = "#b1bac4"
W, H = COLS * CW + 2 * PAD, ROWS * LH + 2 * PAD  # 504 x 501 → exibido a 370px = ~368px de altura


def placeholder(text):
    """Iniciais grandes e levemente suavizadas, só para o layout não ficar vazio."""
    img = Image.new("L", (900, 900), 0)
    font = None
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ):
        try:
            font = ImageFont.truetype(path, 400)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default(size=400)
    ImageDraw.Draw(img).text((450, 450), text, font=font, fill=255, anchor="mm")
    return img.filter(ImageFilter.GaussianBlur(5))


def to_grid(img):
    """Encaixa a imagem em COLS x ROWS caracteres, corrigindo a proporção do caractere."""
    img = img.convert("L")
    box_w, box_h = COLS, ROWS * (LH / CW)  # caixa em "pixels corrigidos"
    scale = min(box_w / img.width, box_h / img.height)
    gw = max(1, round(img.width * scale))
    gh = max(1, round(img.height * scale * (CW / LH)))
    small = img.resize((gw, gh), Image.BOX)  # média por bloco → menos ruído que LANCZOS
    canvas = Image.new("L", (COLS, ROWS), 0)
    canvas.paste(small, ((COLS - gw) // 2, (ROWS - gh) // 2))
    return canvas


def to_rows(grid):
    px = grid.load()
    n = len(RAMP)
    gamma = float(os.environ.get("ASCII_GAMMA", "0.75"))  # <1 clareia (mais tinta nas sombras), >1 escurece
    rows = []
    for y in range(ROWS):
        line = "".join(
            RAMP[min(n - 1, int((px[x, y] / 255) ** gamma * n))] for x in range(COLS)
        )
        rows.append(line.rstrip())
    return rows


def build_svg(rows):
    clips, texts, cursors = [], [], []
    inner_w = COLS * CW
    for i, line in enumerate(rows):
        if not line.strip():
            continue
        top = PAD + i * LH
        begin, dur = 0.3 + i * 0.045, 0.5
        clip_anim = (
            ""
            if STATIC
            else f'<animate attributeName="width" from="0" to="{inner_w}" begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/>'
        )
        clips.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{top - 0.5:.1f}" width="{inner_w if STATIC else 0}" height="{LH + 1}">{clip_anim}</rect></clipPath>'
        )

        # Cada trecho contínuo de texto é posicionado explicitamente em x, então o resultado
        # não depende de como o renderizador trata espaços (e a deriva de fonte é mínima).
        segs, pos = [], 0
        for tok in re.split(r"( {2,})", line):
            if not tok:
                continue
            if tok.startswith("  "):
                pos += len(tok)
                continue
            lead = len(tok) - len(tok.lstrip(" "))
            body = tok.strip(" ")
            x = PAD + (pos + lead) * CW
            esc = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "\u00a0")
            segs.append(
                f'<text x="{x:.1f}" y="{top + LH - 1.8:.1f}">{esc}</text>'
            )
            pos += len(tok)
        texts.append(f'<g clip-path="url(#r{i})">{"".join(segs)}</g>')

        if not STATIC:  # cursor de bloco que acompanha a borda da revelação
            end = begin + dur
            cursors.append(
                f'<rect x="{PAD}" y="{top:.1f}" width="{CW}" height="{LH - 1}" fill="{INK}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
                f'<animate attributeName="x" from="{PAD}" to="{PAD + inner_w}" begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{end:.2f}s"/></rect>'
            )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="Retrato em arte ASCII">
<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS}px;fill:{INK}}}</style>
<defs>{"".join(clips)}</defs>
<rect x=".5" y=".5" width="{W - 1:.0f}" height="{H - 1:.0f}" rx="12" fill="#0d1117" stroke="#30363d"/>
{chr(10).join(texts)}
{chr(10).join(cursors)}
</svg>
'''


def main():
    if "--text" in sys.argv:
        img = placeholder(sys.argv[sys.argv.index("--text") + 1])
        print("modo placeholder (--text)")
    elif SRC.exists():
        img = Image.open(SRC)
    else:
        img = placeholder("KG")
        print("source-prepped.png não encontrado — gerando placeholder com iniciais.")
        print("Para usar a sua foto: python scripts/prep_photo.py source-photo.jpg")
    rows = to_rows(to_grid(img))
    OUT.write_text(build_svg(rows), encoding="utf-8")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
