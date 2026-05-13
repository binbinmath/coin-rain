"""把根目录的 coin_e.png（黑底原图）做成透明背景的 fine999.png。

之前 coins_clean/fine999.png 是按"像素颜色"抠的，金币内部偏暗的刻字也被抠掉了。
这里改成"圆形 alpha 蒙版"：先识别金币的圆心和半径，然后用整圆覆盖 alpha=255，
这样金币本体（含内部所有刻字、纹理、阴影）100% 保留。

用法（仓库根目录）：
    python scripts/extract_fine999.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "coin_e.png"
DST = REPO / "assets" / "coins" / "fine999.png"

OUT_SIZE = 256
BG_THRESHOLD = 110   # 110 跳过金币周围的发光 halo，只圈金币本体


def main() -> None:
    img = Image.open(SRC).convert("RGB")
    arr = np.array(img)
    W, H = img.size

    gray = arr.mean(axis=2)
    bright = gray > BG_THRESHOLD
    ys, xs = np.where(bright)
    if xs.size == 0:
        raise SystemExit("没找到亮像素，是不是图全黑？")

    # 用 bbox 的中心和最大边长作为圆心 / 直径
    x_lo, x_hi = xs.min(), xs.max()
    y_lo, y_hi = ys.min(), ys.max()
    cx = (x_lo + x_hi) / 2
    cy = (y_lo + y_hi) / 2
    diameter = max(x_hi - x_lo, y_hi - y_lo)
    r = diameter / 2 + 4  # 多 4 px 包住外圈倒角

    print(f"coin center: ({cx:.0f}, {cy:.0f}), radius: {r:.0f}px (in {W}×{H})")

    # 圆形 alpha 蒙版 + 轻羽化抗锯齿
    alpha = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(alpha)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=2))

    out = img.convert("RGBA")
    out.putalpha(alpha)

    # 裁中心方形区域（边长略大于直径）再缩到 OUT_SIZE × OUT_SIZE
    half = int(r + 8)
    box = (
        max(0, int(cx - half)),
        max(0, int(cy - half)),
        min(W, int(cx + half)),
        min(H, int(cy + half)),
    )
    cropped = out.crop(box)
    final = cropped.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    DST.parent.mkdir(parents=True, exist_ok=True)
    final.save(DST, "PNG", optimize=True, compress_level=9)
    print(f"wrote {DST}  ({DST.stat().st_size / 1024:.0f} KB, {OUT_SIZE}×{OUT_SIZE})")


if __name__ == "__main__":
    main()
