"""把 Kenney CC0 的筹码落桌录音叠成老虎机转动音效（slot_spin.wav）。

为什么用筹码声当 slot 咔哒的素材？
  - 真实机械金属落桌的录音，干净、有质感，比纯合成的"噪声+正弦"听感强太多
  - 每个 click ~150-300ms，留前 80ms 的 transient 当作单击 → 节奏可控

老虎机经典上瘾感来自：
  1. 干净的"咔哒"金属感（筹码音满足）
  2. 节奏从快到慢的减速（与中央 reel 滚动同步）
  3. 几声 settle 末尾的清脆 ding（FM 钟铃合成补一层）

源：Kenney - Casino Audio (CC0)
   https://kenney.nl/assets/casino-audio
   data/slot_clicks/ 里有用到的 7 个 ogg

用法（仓库根目录）：
    python scripts/gen_slot_spin.py
"""
from __future__ import annotations

import math
import random
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "data" / "slot_clicks"
OUT = REPO / "assets" / "slot_spin.wav"

SR = 44100
DURATION = 2.4
SEED = 20260428

# 节奏：开头 22 次/秒，末尾减到 5 次/秒
RATE_START = 22.0
RATE_END = 5.0

# 末尾 settle 钟铃位置（reel 在视觉上 settle 的时间点：60%/73%/87%/100%）
BELL_TIMES = [0.60, 0.733, 0.867, 1.0]
BELL_FREQ_BASE = 1800.0   # 钟铃基频
BELL_FREQ_STEP = 220.0    # 每次 settle 升高的频率（4 个 ding 是上行琶音）


def _load_clicks() -> list[np.ndarray]:
    """加载所有筹码 ogg，剪到只剩 transient（前 80ms），加 fade out 避免爆音。"""
    files = sorted(SRC_DIR.glob("*.ogg"))
    if not files:
        raise SystemExit(
            f"找不到筹码 ogg。请先把 Kenney Casino Audio 的 chip-lay-* / chips-stack-* "
            f"放到 {SRC_DIR}\n源：https://kenney.nl/assets/casino-audio (CC0)"
        )
    out = []
    transient_max = int(0.08 * SR)  # 80 ms
    for f in files:
        data, sr = sf.read(str(f))
        if sr != SR:
            raise SystemExit(f"{f.name} 采样率 {sr} != {SR}")
        if data.ndim == 2:
            data = data.mean(axis=1)
        data = data.astype(np.float32)
        # 剪到峰值附近 + 前 80ms
        peak = int(np.argmax(np.abs(data)))
        start = max(0, peak - 20)
        end = min(len(data), start + transient_max)
        clip = data[start:end].copy()
        # 末尾加 fade out（最后 20 个采样）
        fade_n = min(20, len(clip))
        clip[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)
        out.append(clip)
    return out


def _bell(freq: float, dur_s: float = 0.55) -> np.ndarray:
    """FM 钟铃合成：carrier=freq、modulator=freq*1.5、indent decay。"""
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    # 包络：尖锐 attack + 长尾指数衰减
    env = np.exp(-t * 4.5).astype(np.float32) * np.minimum(t / 0.005, 1.0).astype(np.float32)
    # 调制深度也跟着 envelope 衰减（钟铃音色明亮 → 暗的过程）
    mod_index = (8.0 * np.exp(-t * 6.0)).astype(np.float32)
    sig = np.sin(2.0 * math.pi * freq * t + mod_index * np.sin(2.0 * math.pi * freq * 1.5 * t))
    return (sig * env).astype(np.float32)


def synth() -> np.ndarray:
    rng = random.Random(SEED)
    clicks = _load_clicks()
    n_total = int(DURATION * SR)
    audio = np.zeros(n_total, dtype=np.float32)

    # ---- 1. 主咔哒节奏（确定性间隔，不随机抖，让减速感清晰） ----
    t = 0.04
    while t < DURATION - 0.05:
        p = t / DURATION
        # 与 reel 视觉一致：用 ease-out 速度反推 click rate
        rate = RATE_START * (1.0 - p) ** 1.5 + RATE_END * (p ** 0.6)
        rate = max(rate, 4.0)
        click = clicks[rng.randrange(len(clicks))]
        gain = rng.uniform(0.70, 1.0)
        start = int(t * SR)
        end = min(start + len(click), n_total)
        audio[start:end] += click[: end - start] * gain
        t += 1.0 / rate

    # ---- 2. 末尾 settle 钟铃：4 声上行琶音，对应 4 位数字依次定格 ----
    for i, frac in enumerate(BELL_TIMES):
        center_t = DURATION * frac
        freq = BELL_FREQ_BASE + i * BELL_FREQ_STEP
        bell = _bell(freq, dur_s=0.55)
        # 钟铃音量 25% 比咔哒小一截，做点缀不抢主旋
        gain = 0.30
        start = int(center_t * SR)
        end = min(start + len(bell), n_total)
        audio[start:end] += bell[: end - start] * gain

    # ---- 归一化 ----
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
    print("source: Kenney - Casino Audio (CC0) + FM bell synth")


if __name__ == "__main__":
    main()
