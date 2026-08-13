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
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError(f"araç bulunamadı (kurulu değil?): {cmd[0]}")
    if log_path:
        Path(log_path).write_text(
            f"$ {' '.join(cmd)}\n\n[STDOUT]\n{proc.stdout}\n\n[STDERR]\n{proc.stderr}\n"
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Komut başarısız (exit {proc.returncode}): {' '.join(cmd)}\n{proc.stderr[-2000:]}"
        )
    return proc


def run_redirect(cmd: list[str], out_path: str | Path,
                 log_path: str | Path | None = None) -> None:
    """Komutu çalıştır, stdout'u out_path'e yaz (filtlong/mash dist gibi)."""
    try:
        with open(out_path, "wb") as out:
            proc = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise RuntimeError(f"araç bulunamadı (kurulu değil?): {cmd[0]}")
    if log_path:
        Path(log_path).write_text(
            f"$ {' '.join(cmd)} > {out_path}\n\n[STDERR]\n{proc.stderr.decode(errors='replace')}\n"
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Komut başarısız (exit {proc.returncode}): {' '.join(cmd)}\n"
            f"{proc.stderr.decode(errors='replace')[-2000:]}"
        )


def run_pipe(cmd1: list[str], cmd2: list[str], out_path: str | Path,
             log_path: str | Path | None = None) -> None:
    """cmd1 | cmd2 (iki-süreç pipe); cmd2 stdout → out_path. Shell yok (subprocess list).
    `samtools mpileup | ivar consensus` gibi araçlar için; herhangi biri hata verirse YÜKSEK SESLE fırlat."""
    try:
        with open(out_path, "wb") as out:
            p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out, stderr=subprocess.PIPE)
            p1.stdout.close()  # p2 EOF alabilsin
            err2 = p2.communicate()[1]
            err1 = p1.communicate()[1]
    except FileNotFoundError as exc:
        raise RuntimeError(f"araç bulunamadı (kurulu değil?): {exc.filename or cmd1[0]}")
    if log_path:
        Path(log_path).write_text(
            f"$ {' '.join(cmd1)} | {' '.join(cmd2)} > {out_path}\n\n"
            f"[STDERR cmd1]\n{(err1 or b'').decode(errors='replace')}\n\n"
            f"[STDERR cmd2]\n{(err2 or b'').decode(errors='replace')}\n"
        )
    if p1.returncode not in (0, None):
        raise RuntimeError(f"Pipe 1. komut başarısız (exit {p1.returncode}): {' '.join(cmd1)}")
    if p2.returncode != 0:
        raise RuntimeError(
            f"Pipe 2. komut başarısız (exit {p2.returncode}): {' '.join(cmd2)}\n"
            f"{(err2 or b'').decode(errors='replace')[-2000:]}"
        )


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
