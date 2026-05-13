"""把 6 张金币 PNG 合成一张 3x2 网格图，用于公众号文章 [图位 4]。

输出: 公众号文章/截图/coins_grid.png
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "公众号文章" / "截图" / "coins"
OUT = ROOT / "公众号文章" / "截图" / "coins_grid.png"

# 顺序：让"古钱"和"洋钱"分行，视觉对仗
# 第一行：大唐 / 大宋 / 千足金（中国线 + 现代）
# 第二行：Sovereign / Ducat / Napoleon（西方金币）
ORDER = [
    "datang.png",
    "song.png",
    "fine999.png",
    "sovereign.png",
    "ducat.png",
    "napoleon.png",
]

CELL = 480              # 每个单元格统一尺寸（在最大原图基础上不放大）
MARGIN_OUT = 30         # 整张图外边距
GAP = 24                # 单元格间距
BG = (12, 11, 10, 255)  # 与项目主题一致的墨黑底（#0c0b0a）


def main() -> None:
    cols, rows = 3, 2
    canvas_w = MARGIN_OUT * 2 + CELL * cols + GAP * (cols - 1)
    canvas_h = MARGIN_OUT * 2 + CELL * rows + GAP * (rows - 1)

    canvas = Image.new("RGBA", (canvas_w, canvas_h), BG)

    for i, name in enumerate(ORDER):
        im = Image.open(SRC / name).convert("RGBA")
        # 等比缩放到 CELL（保持比例，居中放）
        im.thumbnail((CELL, CELL), Image.LANCZOS)
        col = i % cols
        row = i // cols
        cell_x = MARGIN_OUT + col * (CELL + GAP)
        cell_y = MARGIN_OUT + row * (CELL + GAP)
        # 把 im 居中到这个 CELL×CELL 的格子里
        x = cell_x + (CELL - im.width) // 2
        y = cell_y + (CELL - im.height) // 2
        canvas.alpha_composite(im, (x, y))

    # 转 RGB 后存 PNG（透明底其实没必要在文章里）
    canvas.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT}  ({canvas_w}x{canvas_h})")


if __name__ == "__main__":
    main()
