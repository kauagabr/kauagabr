#!/usr/bin/env python3
"""Prepara a foto para virar ASCII: remove fundo, realça contraste local e põe sobre preto.

Uso:  python scripts/prep_photo.py source-photo.jpg [--zoom 1.25]
Saída: source-prepped.png (tons de cinza)

--zoom N   aproxima do rosto/ombros (recorta um quadrado de 1/N do lado, ancorado no topo).
           Útil quando o rosto ocupa pouco da foto. Padrão: 1.0 (sem zoom).

Se `rembg` / `opencv-python` não estiverem instalados, o script segue com alternativas
mais simples (sem recorte do fundo / contraste global).
"""
import os
import sys
from pathlib import Path

from PIL import Image, ImageOps

OUT = Path(__file__).resolve().parent.parent / "source-prepped.png"


def main(src, zoom=1.0):
    img = Image.open(src).convert("RGB")
    alpha = None

    # 1) remove o fundo para isolar a pessoa
    try:
        from rembg import new_session, remove

        # Modelo leve (~175 MB) feito para pessoas. O padrão das versões novas do
        # rembg é um modelo de ~1 GB que pode estourar a memória de muita máquina.
        session = new_session(os.environ.get("REMBG_MODEL", "u2net_human_seg"))
        alpha = remove(img, session=session).split()[-1]
        bbox = alpha.getbbox()
        if bbox:  # recorta com ~8% de folga
            pad = int(0.08 * max(bbox[2] - bbox[0], bbox[3] - bbox[1]))
            box = (
                max(bbox[0] - pad, 0),
                max(bbox[1] - pad, 0),
                min(bbox[2] + pad, img.width),
                min(bbox[3] + pad, img.height),
            )
            img, alpha = img.crop(box), alpha.crop(box)
    except ImportError:
        print("aviso: rembg não instalado — o fundo será mantido (use uma foto de fundo liso).")

    gray = img.convert("L")

    # 2) CLAHE: dá luzes e sombras reais a rostos iluminados de forma chapada
    try:
        import cv2
        import numpy as np

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        # mistura 60% CLAHE + 40% original: mantém o realce sem amplificar a textura do tecido
        gray = Image.blend(gray, Image.fromarray(clahe.apply(np.array(gray))), 0.6)
    except ImportError:
        print("aviso: opencv não instalado — usando contraste global.")
        gray = ImageOps.autocontrast(ImageOps.equalize(gray), cutoff=1)

    # 3) compõe sobre preto puro. O cartão ASCII é escuro (tinta clara), então o claro vira
    #    caractere denso e o fundo preto vira espaço vazio.
    if alpha is not None:
        gray = Image.composite(gray, Image.new("L", gray.size, 0), alpha)

    if zoom > 1.0:  # recorte quadrado ancorado no topo, centralizado na horizontal
        side = int(min(gray.width, gray.height) / zoom)
        left = (gray.width - side) // 2
        gray = gray.crop((left, 0, left + side, side))

    gray.save(OUT)
    print(f"→ {OUT} ({gray.width}x{gray.height})")


if __name__ == "__main__":
    args = sys.argv[1:]
    zoom = 1.0
    if "--zoom" in args:
        i = args.index("--zoom")
        zoom = float(args[i + 1])
        del args[i : i + 2]
    if len(args) != 1:
        sys.exit("uso: python scripts/prep_photo.py caminho/da/foto.jpg [--zoom 1.25]")
    main(args[0], zoom)
