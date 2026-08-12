"""Config yükleme: default.yaml + kullanıcı YAML derin-merge, nokta-yollu erişim."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"


def _deep_merge(base: dict, override: dict) -> dict:
    """override'ı base üstüne derin-merge et (override kazanır)."""
    out = copy.deepcopy(base)
    for key, val in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def load_config(path: str | Path | None = None,
                default_path: str | Path | None = None) -> dict:
    """default.yaml'ı yükle, verilirse kullanıcı config'iyle ez."""
    dpath = Path(default_path) if default_path else _DEFAULT_PATH
    with open(dpath) as fh:
        cfg = yaml.safe_load(fh) or {}
    if path:
        with open(path) as fh:
            user = yaml.safe_load(fh) or {}
        cfg = _deep_merge(cfg, user)
    return cfg


def get(cfg: dict, dotted: str, default: Any = None) -> Any:
    """Nokta-yollu erişim: get(cfg, 'tools.spades.careful', False)."""
    node: Any = cfg
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node
