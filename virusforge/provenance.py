"""Provenance kaydı: her sonuç tool+DB sürümü ve parametreleriyle izlenebilir."""
from __future__ import annotations

import json
from pathlib import Path

from . import util

_FIELDS = (
    "module", "tool", "version", "database", "database_version",
    "command", "params", "input_sha256", "output_sha256", "timestamp",
)


def record(module: str, tool: str, version: str | None = None,
           database: str | None = None, database_version: str | None = None,
           command: str | None = None, params: dict | None = None,
           input_sha256: str | None = None, output_sha256: str | None = None) -> dict:
    """Tek bir provenance kaydı üret (tüm alanlar mevcut; uydurma YOK, yoksa None)."""
    return {
        "module": module,
        "tool": tool,
        "version": version,
        "database": database,
        "database_version": database_version,
        "command": command,
        "params": params or {},
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "timestamp": util.utc_now(),
    }


def write(run_dir: str | Path, records: list[dict]) -> Path:
    """provenance.json'u run dizinine yaz."""
    out = Path(run_dir) / "provenance.json"
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    return out
