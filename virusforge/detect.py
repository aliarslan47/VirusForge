"""V00 otomatik tespit: read-tipi (short/long/hybrid/assembly)."""
from __future__ import annotations

import gzip
from pathlib import Path

from . import config, util

SHORT_READ = "SHORT_READ"
LONG_READ = "LONG_READ"
HYBRID = "HYBRID"
ASSEMBLY_INPUT = "ASSEMBLY_INPUT"

_OVERRIDE = {
    "short": SHORT_READ, "long": LONG_READ,
    "hybrid": HYBRID, "assembly": ASSEMBLY_INPUT,
}


def _open(p: Path):
    return gzip.open(p, "rt") if p.name.endswith(".gz") else open(p)


def mean_read_length(fastq: Path, sample_n: int = 200) -> float:
    """İlk N read'in ortalama uzunluğu."""
    lengths: list[int] = []
    with _open(fastq) as fh:
        for i, line in enumerate(fh):
            if i % 4 == 1:  # sequence satırı
                lengths.append(len(line.strip()))
            if len(lengths) >= sample_n:
                break
    return sum(lengths) / len(lengths) if lengths else 0.0


def _is_assembly(sample_dir: Path) -> bool:
    for p in sample_dir.iterdir():
        if p.name.lower().endswith((".fasta", ".fa", ".fna")):
            return True
    return False


def detect_mode(sample_dir: str | Path, cfg: dict | None = None) -> dict:
    """Modu belirle. Kullanıcı override (general.mode) önceliklidir; dosya adı tek başına karar vermez."""
    d = Path(sample_dir)
    cfg = cfg or config.load_config()
    override = config.get(cfg, "general.mode", "auto")
    if override in _OVERRIDE:
        return {"mode": _OVERRIDE[override], "evidence": {"source": "config_override"}}

    short = util.find_short_reads(d)
    long_r = util.find_long_reads(d)
    short_max = config.get(cfg, "detect.short_max_len", 500)
    long_min = config.get(cfg, "detect.long_min_len", 1000)

    ev: dict = {}
    short_ok = False
    long_ok = False
    if short:
        ml = mean_read_length(short[0])
        ev["short_mean_len"] = round(ml, 1)
        short_ok = ml <= short_max
    if long_r:
        ml = mean_read_length(long_r)
        ev["long_mean_len"] = round(ml, 1)
        long_ok = ml >= long_min

    if short_ok and long_ok:
        mode = HYBRID
    elif long_ok:
        mode = LONG_READ
    elif short_ok:
        mode = SHORT_READ
    elif _is_assembly(d) and not short and not long_r:
        mode = ASSEMBLY_INPUT
    elif short:
        mode = SHORT_READ
    elif long_r:
        mode = LONG_READ
    else:
        mode = ASSEMBLY_INPUT
    ev["source"] = "auto"
    return {"mode": mode, "evidence": ev}
