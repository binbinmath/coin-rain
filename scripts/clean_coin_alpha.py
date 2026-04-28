"""统一清理 assets/coins/*.png 的边缘黑圈 / halo。

策略：
  1. 识别图像里"亮像素"的 bbox（排除纯黑背景），算出圆心 + 半径
  2. 用圆形 alpha mask（半径再内缩 INSET_PX 防止边缘黑圈/阴影残留）
  3. 圆内保留原 alpha，圆外强制透明
  4. 边缘做高斯模糊（1.2px）做抗锯齿
  5. 顺便重新 LANCZOS 缩放到 OUT_SIZE 保证统一规格

用法（仓库根目录）：
    python scripts/clean_coin_alpha.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent
COINS_DIR = REPO / "assets" / "coins"

COIN_FILES = ("datang.png", "song.png", "ducat.png", "sovereign.png", "napoleon.png", "fine999.png")

OUT_SIZE = 256
INSET_PX = 6           # 圆形 mask 比识别出的圆再内缩这些 px，吃掉边缘黑色
BG_THRESHOLD = 80      # RGB 平均亮度大于这个值才算"金币本体"，过滤掉黑边


def clean_one(path: Path) -> None:
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    W, H = img.size

    rgb_mean = arr[:, :, :3].mean(axis=2)
    a = arr[:, :, 3]
    bright = (rgb_mean > BG_THRESHOLD) & (a > 50)
    ys, xs = np.where(bright)
    if xs.size == 0:
        print(f"{path.name}: no bright pixels found, skipped")
        return

    x_lo, x_hi = xs.min(), xs.max()
    y_lo, y_hi = ys.min(), ys.max()
    cx = (x_lo + x_hi) / 2
    cy = (y_lo + y_hi) / 2
    # 取 bbox 较小那条边的一半为半径，再内缩 INSET_PX
    radius = max(8.0, min(x_hi - x_lo, y_hi - y_lo) / 2 - INSET_PX)

    circle = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(circle)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255)
    circle = circle.filter(ImageFilter.GaussianBlur(radius=1.2))
    circle_arr = np.array(circle)

    # 圆外强制透明；圆内保留原 alpha 与圆形 mask 的较小值（让边缘平滑）
    new_alpha = np.minimum(circle_arr, a)
    arr[:, :, 3] = new_alpha

    out = Image.fromarray(arr, "RGBA")
    # 裁中心方形并缩到 OUT_SIZE
    half = int(radius + INSET_PX + 4)
    box = (
        max(0, int(cx - half)),
        max(0, int(cy - half)),
        min(W, int(cx + half)),
        min(H, int(cy + half)),
    )
    out = out.crop(box).resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    out.save(path, "PNG", optimize=True, compress_level=9)
    print(f"{path.name}: c=({cx:.0f},{cy:.0f}) r={radius:.0f}px → {OUT_SIZE}×{OUT_SIZE}, "
          f"{path.stat().st_size / 1024:.0f} KB")


def main() -> None:
    for name in COIN_FILES:
        path = COINS_DIR / name
        if not path.exists():
            print(f"skip missing: {name}")
            continue
        clean_one(path)


if __name__ == "__main__":
    main()
