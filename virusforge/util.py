"""Ortak yardımcılar: hash, komut çalıştırma, okuma dosyası bulma."""
from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Illumina/ONT dosya işaretleri
_R1_PAT = ("_r1", "_1.", ".r1.", "_r1_")
_R2_PAT = ("_r2", "_2.", ".r2.", "_r2_")
_LONG_HINTS = ("ont", "nanopore", "minion", "promethion", "long", "pacbio", "hifi")
_FASTQ_SUF = (".fastq", ".fq", ".fastq.gz", ".fq.gz")


def utc_now() -> str:
    """ISO-8601 UTC zaman damgası (provenance için)."""
    return datetime.now(timezone.utc).isoformat()


def sha256(path: str | Path) -> str:
    """Dosyanın SHA-256 özeti."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(cmd: list[str], cwd: str | Path | None = None,
            log_path: str | Path | None = None) -> subprocess.CompletedProcess:
    """Komutu çalıştır; stdout/stderr'i log'a yaz; hata olursa YÜKSEK SESLE fırlat."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if log_path:
        Path(log_path).write_text(
            f"$ {' '.join(cmd)}\n\n[STDOUT]\n{proc.stdout}\n\n[STDERR]\n{proc.stderr}\n"
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Komut başarısız (exit {proc.returncode}): {' '.join(cmd)}\n{proc.stderr[-2000:]}"
        )
    return proc


def _is_fastq(p: Path) -> bool:
    name = p.name.lower()
    return any(name.endswith(s) for s in _FASTQ_SUF)


def find_short_reads(sample_dir: str | Path) -> tuple[Path, Path] | None:
    """R1/R2 çiftini bul; yoksa None."""
    d = Path(sample_dir)
    fastqs = [p for p in sorted(d.iterdir()) if _is_fastq(p)]
    r1 = next((p for p in fastqs if any(t in p.name.lower() for t in _R1_PAT)), None)
    r2 = next((p for p in fastqs if any(t in p.name.lower() for t in _R2_PAT)), None)
    if r1 and r2:
        return r1, r2
    return None


def find_long_reads(sample_dir: str | Path) -> Path | None:
    """Uzun-okuma dosyasını bul. R1/R2'yi DIŞLA (BacForge dersi: R1 de .fastq)."""
    d = Path(sample_dir)
    fastqs = [p for p in sorted(d.iterdir()) if _is_fastq(p)]
    non_paired = [
        p for p in fastqs
        if not any(t in p.name.lower() for t in _R1_PAT + _R2_PAT)
    ]
    # önce açık long ipuçlu dosya
    hinted = [p for p in non_paired if any(h in p.name.lower() for h in _LONG_HINTS)]
    if hinted:
        return hinted[0]
    # tek başına, eşleşmemiş fastq → long adayı
    if len(non_paired) == 1:
        return non_paired[0]
    return None
