"""Tool/DB metadata registry + gerçek sürüm tespiti (uydurma YOK)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

_REGISTRY_PATH = Path(__file__).resolve().parent / "data" / "registry.yaml"
_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        with open(_REGISTRY_PATH) as fh:
            _cache = yaml.safe_load(fh) or {}
    return _cache


def tool(name: str) -> dict:
    """Aracın metadata'sı; bilinmiyorsa KeyError (yüksek sesle)."""
    reg = _load()
    if name not in reg:
        raise KeyError(f"registry'de bilinmeyen tool: {name}")
    return reg[name]


import re

_NOISE = ("warning", "usage", "error", "traceback", "note:")
_VERSION_RE = re.compile(r"v?\d+\.\d+[\w.\-]*")


def _parse_version(text: str) -> str | None:
    """Sürüm çıktısından temiz token çıkar: uyarı/yardım satırlarını atla, sürüm-benzeri
    (vN.N…) token'ı seç. Sürüm yoksa None (çöp/yardım metni gösterme)."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    clean = [ln for ln in lines if not ln.lower().startswith(_NOISE)]
    for ln in (clean or lines):
        m = _VERSION_RE.search(ln)
        if m:
            return m.group(0)
    return None


def detect_version(name: str) -> str | None:
    """Araç kuruluysa sürüm string'i, değilse None (asla uydurma)."""
    meta = tool(name)
    cmd = meta.get("version_cmd")
    if not cmd:
        return None
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return _parse_version(proc.stdout or proc.stderr or "")
