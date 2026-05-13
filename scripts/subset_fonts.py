"""把嵌入字体裁到只剩项目实际用到的字符。

思路：
  1. 扫描所有 .py / .qss 源码，提取出现过的中文字符 + ASCII 可见字符 + 常见标点
  2. 加入金币背面汉字（开 / 元 / 通 / 宝 / 永 / 乐 / 宣 / 和 / 壹 / 圓）作为 V1 兼容
  3. 加入数字、字母、必要符号
  4. 用 fontTools 的 pyftsubset 跑裁剪

效果（预期）：
  Noto Serif SC: 24 MB → < 500 KB
  Fraunces:      376 KB → < 80 KB

用法（仓库根目录）：
  pip install fonttools brotli
  python scripts/subset_fonts.py
"""
from __future__ import annotations

import re
import string
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "assets" / "fonts"
OUT = SRC  # 裁完直接覆盖原文件名（保留带 -Subset 后缀的备份）

# 项目里实际用到的中文短语（从源码扫到的字 + 这里手工补一些保险字）
SAFETY_CJK = "开元通宝永乐宣和壹圓今日到账当前已经进账天年月日时分秒"


def _scan_source_chars() -> str:
    """扫描所有 py + qss 源码文件，返回出现过的所有字符。"""
    blob = []
    for p in REPO.glob("*.py"):
        blob.append(p.read_text(encoding="utf-8"))
    qss = REPO / "style.qss"
    if qss.exists():
        blob.append(qss.read_text(encoding="utf-8"))
    text = "".join(blob)
    return text


def _build_charset() -> set[str]:
    chars: set[str] = set()
    text = _scan_source_chars()
    for c in text:
        # 中文 + 中日韩通用标点
        if "一" <= c <= "鿿":
            chars.add(c)
        elif "　" <= c <= "〿":  # CJK 标点
            chars.add(c)
        elif c in "·×—↗↩→←↑↓✦":
            chars.add(c)
    # 全部 ASCII 可见 + 几个常用符号
    chars.update(string.printable.replace("\t", "").replace("\n", "").replace("\r", "").replace("\x0b", "").replace("\x0c", ""))
    # 保险字
    chars.update(SAFETY_CJK)
    # 全角符号
    chars.update("，。：；！？（）【】「」『』《》、…")
    return chars


def subset(src: Path, dst: Path, chars: set[str], extra_args: list[str] | None = None) -> None:
    text = "".join(sorted(chars))
    args = [
        sys.executable, "-m", "fontTools.subset",
        str(src),
        f"--output-file={dst}",
        f"--text={text}",
        "--layout-features=*",
        "--no-hinting",
        "--desubroutinize",
        "--name-IDs=*",
        "--glyph-names",
        "--symbol-cmap",
        "--legacy-cmap",
        "--notdef-glyph",
        "--notdef-outline",
        "--recommended-glyphs",
        "--drop-tables=DSIG",
    ]
    if extra_args:
        args.extend(extra_args)
    subprocess.run(args, check=True)


def main() -> None:
    chars = _build_charset()
    print(f"字符集：{len(chars)} 个")

    pairs = [
        (SRC / "NotoSerifSC-VariableFont.ttf", OUT / "NotoSerifSC-Subset.ttf"),
        (SRC / "Fraunces-VariableFont.ttf",    OUT / "Fraunces-Subset.ttf"),
    ]
    for src, dst in pairs:
        if not src.exists():
            print(f"缺源字体：{src}，跳过")
            continue
        old = src.stat().st_size
        subset(src, dst, chars)
        new = dst.stat().st_size
        print(f"{src.name}: {old/1024:.0f} KB → {new/1024:.0f} KB ({100*new/old:.1f}%)")


if __name__ == "__main__":
    main()
