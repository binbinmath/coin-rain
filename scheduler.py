"""Windows 任务计划封装 · schtasks.exe subprocess。

对外提供：
- register(cfg): 根据 Config 注册任务（单次 1 个，多次 N 个独立任务）
- enable() / disable(): 启/停所有相关任务
- status(): 查询任务是否存在、是否启用、下次触发时间
- unregister(): 清掉全部相关任务
- _distribute_times(): 纯函数，多次模式均匀分布时间点
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import Config


TASK_NAME_BASE = "CoinRainDaily"


class SchedulerError(RuntimeError):
    pass


@dataclass
class TaskStatus:
    exists: bool
    enabled: bool
    next_run: datetime | None


# ---------- 纯函数 ----------

def _distribute_times(first: str, last: str, count: int) -> list[str]:
    """在 [first, last] 区间上均匀分布 count 个时间点（首尾含）。

    - first/last 格式 "HH:MM"
    - count >= 2
    - 分钟向最近整数四舍五入
    """
    fh, fm = map(int, first.split(":"))
    lh, lm = map(int, last.split(":"))
    first_min = fh * 60 + fm
    last_min = lh * 60 + lm
    total_diff = last_min - first_min
    step = total_diff / (count - 1)
    result = []
    for i in range(count):
        m = first_min + round(step * i)
        h, mm = divmod(m, 60)
        result.append(f"{h:02d}:{mm:02d}")
    return result


def _task_names(mode: str, count: int | None) -> list[str]:
    """多次模式返回 N 个任务名；单次返回 1 个。"""
    if mode == "single":
        return [TASK_NAME_BASE]
    return [f"{TASK_NAME_BASE}_{i}" for i in range(1, (count or 1) + 1)]


# ---------- subprocess 封装 ----------

def _run(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _exe_path() -> str:
    """当前运行的 exe 绝对路径（打包态）或脚本绝对路径（开发态）。"""
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(sys.argv[0]).resolve())


# ---------- 对外 API ----------

def status() -> TaskStatus:
    """查询任务状态。"""
    cfg = Config.load()
    if cfg is None:
        # 无 config 时尝试查基础任务名
        return _single_task_status(TASK_NAME_BASE)

    names = _task_names(cfg.mode, cfg.count)
    any_exists = False
    all_enabled = True
    earliest: datetime | None = None
    for name in names:
        s = _single_task_status(name)
        if not s.exists:
            continue
        any_exists = True
        if not s.enabled:
            all_enabled = False
        if s.next_run and (earliest is None or s.next_run < earliest):
            earliest = s.next_run
    return TaskStatus(exists=any_exists, enabled=(any_exists and all_enabled), next_run=earliest)


def _single_task_status(name: str) -> TaskStatus:
    r = _run(["schtasks.exe", "/Query", "/TN", name, "/FO", "LIST", "/V"])
    if r.returncode != 0:
        return TaskStatus(exists=False, enabled=False, next_run=None)
    enabled = True
    next_run: datetime | None = None
    for line in r.stdout.splitlines():
        s = line.strip()
        sl = s.lower()
        # 英文与中文都尝试
        if sl.startswith("scheduled task state") or s.startswith("任务状态"):
            if "disabled" in sl or "已禁用" in s:
                enabled = False
        if sl.startswith("next run time") or s.startswith("下次运行时间"):
            val = line.split(":", 1)[1].strip() if ":" in line else ""
            next_run = _try_parse_datetime(val)
    return TaskStatus(exists=True, enabled=enabled, next_run=next_run)


def _try_parse_datetime(val: str) -> datetime | None:
    for fmt in ("%m/%d/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


def enable() -> None:
    cfg = Config.load()
    if cfg is None:
        return
    for name in _task_names(cfg.mode, cfg.count):
        r = _run(["schtasks.exe", "/Change", "/TN", name, "/ENABLE"])
        if r.returncode != 0 and not _is_not_found(r):
            raise SchedulerError(r.stderr or r.stdout)


def disable() -> None:
    cfg = Config.load()
    if cfg is None:
        return
    for name in _task_names(cfg.mode, cfg.count):
        r = _run(["schtasks.exe", "/Change", "/TN", name, "/DISABLE"])
        if r.returncode != 0 and not _is_not_found(r):
            raise SchedulerError(r.stderr or r.stdout)


def unregister() -> None:
    """删除所有可能的任务名（base + base_1..12）。"""
    candidates = [TASK_NAME_BASE] + [f"{TASK_NAME_BASE}_{i}" for i in range(1, 13)]
    for name in candidates:
        _run(["schtasks.exe", "/Delete", "/F", "/TN", name])  # 忽略失败


def register(cfg: Config) -> None:
    """根据 config 注册任务。先卸载旧的。"""
    unregister()
    exe = _exe_path()
    if cfg.mode == "single":
        _register_one(TASK_NAME_BASE, exe, cfg.time, nth=1, total=1)
    else:
        times = _distribute_times(cfg.first_time, cfg.last_time, cfg.count)
        for i, t in enumerate(times, start=1):
            _register_one(f"{TASK_NAME_BASE}_{i}", exe, t, nth=i, total=cfg.count)


def _register_one(name: str, exe: str, time: str, nth: int, total: int) -> None:
    tr = f'"{exe}" --rain --nth={nth} --total={total}'
    r = _run([
        "schtasks.exe", "/Create", "/F", "/TN", name,
        "/SC", "DAILY", "/ST", time, "/TR", tr, "/RL", "LIMITED",
    ])
    if r.returncode != 0:
        raise SchedulerError(r.stderr or r.stdout)


def _is_not_found(r: subprocess.CompletedProcess) -> bool:
    msg = (r.stderr or r.stdout or "").lower()
    return "cannot find" in msg or "不存在" in (r.stderr or r.stdout or "") or "找不到" in (r.stderr or r.stdout or "")
