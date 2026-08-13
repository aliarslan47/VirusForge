"""Çoklu-örnek karşılaştırma: birden çok tamamlanmış koşuyu birlikte karşılaştır
(ortak filogenetik ağaç + örnekler-arası benzerlik matrisi + ICTV özet).

Per-örnek V-modülleri (V00–V10) dokunulmaz; bu ayrı bir komuttur (CLI `compare`).
Ağ gerektirmez (yerel MAFFT/IQ-TREE2/blastn).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import tools, util
from .config import get
from .module import safe_run


def parse_blastn_identity(tsv_path) -> dict:
    """all-vs-all blastn (qseqid sseqid pident length) → (q,s) başına uzunluk-ağırlıklı % kimlik."""
    acc: dict[tuple, list] = {}
    for line in Path(tsv_path).read_text().splitlines():
        c = line.split("\t")
        if len(c) < 4:
            continue
        try:
            pid, ln = float(c[2]), float(c[3])
        except ValueError:
            continue
        acc.setdefault((c[0], c[1]), []).append((pid, ln))
    out = {}
    for key, hits in acc.items():
        tot = sum(ln for _, ln in hits)
        out[key] = round(sum(pid * ln for pid, ln in hits) / tot, 3) if tot else 0.0
    return out


def identity_matrix(labels, pairs) -> list:
    """Etiketlerden NxN % kimlik matrisi (köşegen=100, simetrik doldurma)."""
    n = len(labels)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                m[i][j] = 100.0
            else:
                v = pairs.get((labels[i], labels[j])) or pairs.get((labels[j], labels[i]))
                m[i][j] = float(v) if v is not None else 0.0
    return m
