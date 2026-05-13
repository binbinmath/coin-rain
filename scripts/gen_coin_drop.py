"""把 OpenGameArt CC0 的 12 个金币录音混成一个"金币雨"WAV。

- 源：StarNinjas, "12 Coin Sound Effects", CC0
  https://opengameart.org/content/12-coin-sound-effects
- 12 个 ogg（每个 0.3–0.6 秒，44.1kHz / 立体声）
- 把这些 click 按"先密集、中段最密、末尾稀疏"的节奏叠成 6 秒的 mono WAV
- 对齐 rain_window.py 里 heavy / storm 雨势的动画节奏

用法（仓库根目录）：
    1. 解压 starninjas zip 到 data/coin_clicks/coin.*.ogg
    2. python scripts/gen_coin_drop.py
"""
from __future__ import annotations

import math
import random
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "data" / "coin_clicks"          # 12 个 ogg 放这里
OUT = REPO / "assets" / "coin_drop.wav"

SR = 44100
DURATION = 6.0
TRIGGERS_PER_SEC_PEAK = 28.0   # 中段密度峰值
TRIGGERS_PER_SEC_END = 4.0     # 末尾密度
SEED = 20260428


def _density_at(t: float) -> float:
    """t 时刻每秒触发多少个 click。开头有 ~80ms 的快速渐入；中段最密；末尾稀疏。"""
    if t < 0.08:                       # 极短渐入
        return 6.0 + (TRIGGERS_PER_SEC_PEAK - 6.0) * (t / 0.08)
    p = (t - 0.08) / (DURATION - 0.08)
    # 中段最密：先升后降的 sin 拱形
    shaped = math.sin(math.pi * (0.25 + p * 0.6))   # 0.25π → 0.85π
    if shaped < 0:
        shaped = 0
    return TRIGGERS_PER_SEC_END + (TRIGGERS_PER_SEC_PEAK - TRIGGERS_PER_SEC_END) * shaped


def _load_clicks() -> list[np.ndarray]:
    files = sorted(SRC_DIR.glob("coin.*.ogg"))
    if not files:
        raise SystemExit(
            f"找不到金币 ogg。请先把 starninjas zip 解压到 {SRC_DIR}\n"
            "源：https://opengameart.org/content/12-coin-sound-effects（CC0）"
        )
    out = []
    for f in files:
        data, sr = sf.read(str(f))
        if sr != SR:
            raise SystemExit(f"{f.name} 采样率 {sr} != {SR}")
        if data.ndim == 2:                  # stereo → mono
            data = data.mean(axis=1)
        # 修剪开头静音
        idx = np.argmax(np.abs(data) > 0.005)
        data = data[idx:]
        out.append(data.astype(np.float32))
    return out


def synth() -> np.ndarray:
    rng = random.Random(SEED)
    clicks = _load_clicks()
    n_total = int(DURATION * SR)
    audio = np.zeros(n_total, dtype=np.float32)

    # 用累积密度积分采时间点
    triggers: list[float] = []
    t = 0.0
    while t < DURATION - 0.05:
        rate = _density_at(t)
        # 指数分布间隔（rate 高 → 间隔短）
        gap = rng.expovariate(rate)
        t += gap
        if t < DURATION - 0.05:
            triggers.append(t)

    for tt in triggers:
        click = clicks[rng.randrange(len(clicks))]
        gain = rng.uniform(0.45, 1.0)
        # 末尾的金币声音逐渐变小，模拟最后几枚远落的硬币
        tail_fade = 1.0 - max(0.0, (tt - DURATION * 0.75) / (DURATION * 0.25)) * 0.5
        gain *= tail_fade
        start = int(tt * SR)
        end = min(start + len(click), n_total)
        audio[start:end] += click[: end - start] * gain

    # 总体归一化
    peak = float(np.max(np.abs(audio))) or 1.0
    audio = audio * (0.92 / peak)

    return audio


def write_wav(samples: np.ndarray) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(samples * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main() -> None:
    audio = synth()
    write_wav(audio)
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT}  ({len(audio) / SR:.2f}s, {size_kb:.0f} KB, mono / 16-bit / {SR}Hz)")
    print("source: StarNinjas — 12 Coin Sound Effects (CC0)")


if __name__ == "__main__":
    main()
