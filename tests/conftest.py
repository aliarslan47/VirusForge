"""Test yardımcıları: sentetik FASTQ/FASTA üretimi (gerçek veri indirilmez)."""
from pathlib import Path


def write_fastq(path: Path, n: int = 6, length: int = 150) -> Path:
    lines = []
    for i in range(n):
        lines += [f"@read{i}", "A" * length, "+", "I" * length]
    path.write_text("\n".join(lines) + "\n")
    return path


def write_fasta(path: Path, length: int = 5000) -> Path:
    path.write_text(">contig1\n" + "ACGT" * (length // 4) + "\n")
    return path
