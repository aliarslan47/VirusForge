"""Modül taban sınıfı + standart çıktı sözleşmesi + durum kodları."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from . import util

# Standart 8 alt-klasör (tasarım dokümanı Bölüm 3.2)
STANDARD_DIRS = (
    "01_input", "02_work", "03_native_outputs", "04_standardized",
    "05_statistics", "06_visualization", "07_logs", "08_metadata",
)


class Status(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SKIPPED = "SKIPPED"


@dataclass
class ModuleResult:
    status: Status
    summary_path: Path | None = None
    metrics: dict = field(default_factory=dict)


@dataclass
class Context:
    """Modüller arası taşınan bağlam."""
    sample_dir: Path
    run_dir: Path
    cfg: dict
    mode: str = "unknown"
    results: dict = field(default_factory=dict)   # code -> metrics
    artifacts: dict = field(default_factory=dict)  # code -> {isim: yol}
    provenance: list = field(default_factory=list)


class Module:
    """Tüm V-modüllerinin tabanı."""
    name: str = "base"
    code: str = "Vxx"
    dirname: str = "Vxx_MODULE"

    def module_dir(self, run_dir: str | Path) -> Path:
        return Path(run_dir) / self.dirname

    def make_dirs(self, run_dir: str | Path) -> dict[str, Path]:
        """8 standart alt-klasörü oluştur, {isim: yol} döndür."""
        base = self.module_dir(run_dir)
        out: dict[str, Path] = {}
        for d in STANDARD_DIRS:
            p = base / d
            p.mkdir(parents=True, exist_ok=True)
            out[d] = p
        return out

    def write_summary(self, run_dir: str | Path, status: Status,
                      metrics: dict, provenance: list | None = None) -> Path:
        """Vxx_summary.json yaz."""
        base = self.module_dir(run_dir)
        base.mkdir(parents=True, exist_ok=True)
        summary = {
            "module": self.name,
            "code": self.code,
            "status": status.value,
            "metrics": metrics,
            "provenance": provenance or [],
            "timestamp": util.utc_now(),
        }
        out = base / f"{self.code}_summary.json"
        out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        return out

    def is_done(self, run_dir: str | Path) -> bool:
        """Resume için: summary varsa bitmiş say (Kapatma Dayanıklılığı)."""
        return (self.module_dir(run_dir) / f"{self.code}_summary.json").exists()

    def run(self, ctx: Context) -> ModuleResult:  # pragma: no cover - soyut
        raise NotImplementedError
