"""V09 — Karşılaştırmalı Tanımlama & Filogeni (online BLAST + MAFFT/IQ-TREE2 + taxmyPHAGE ICTV).

BLAST = en-yakın-tür seçme + tanımlama; ICTV taksonomi BLAST best-hit'ten TÜRETİLMEZ
(geNomad/PhaBOX/taxmyPHAGE'den gelir). Runtime ağ gerekir (blastn -remote + efetch).
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, latest_genome, safe_run


def parse_blast_hits(tsv_path, n=5) -> list[dict]:
    """blastn tabular (sacc staxids sscinames pident qcovs length evalue bitscore):
    tür başına en iyi hit'i tut, bitscore'a göre sırala, top-N döndür."""
    best: dict[str, dict] = {}
    for line in Path(tsv_path).read_text().splitlines():
        c = line.split("\t")
        if len(c) < 8:
            continue
        acc, species, pident, qcov = c[0], c[2].strip(), c[3], c[4]
        try:
            bit = float(c[7])
        except ValueError:
            continue
        cur = best.get(species)
        if cur is None or bit > cur["_bit"]:
            best[species] = {"accession": acc, "species": species,
                             "identity": pident, "coverage": qcov, "_bit": bit}
    ranked = sorted(best.values(), key=lambda h: -h["_bit"])[:n]
    for h in ranked:
        h.pop("_bit", None)
    return ranked


def parse_iqtree(treefile) -> dict:
    """IQ-TREE2 .treefile (Newick). Ağacı olduğu gibi taşır (görsel render.py'de)."""
    nwk = Path(treefile).read_text().strip()
    return {"newick": nwk, "nearest_sibling": None, "bootstrap": None}


def _first_data_row(path, sep="\t"):
    lines = [ln for ln in Path(path).read_text().splitlines() if ln.strip()]
    if len(lines) < 2:
        return None, None
    return lines[0].split(sep), lines[1].split(sep)


def parse_taxmyphage(out_dir) -> dict:
    """taxmyPHAGE özet tablosu: Genus/Species sütunları (tolerant kolon eşleme)."""
    d = Path(out_dir)
    hit = next((p for p in d.rglob("*axonomy*.tsv")), None) or next((p for p in d.rglob("*.tsv")), None)
    if not hit:
        return {}
    header, row = _first_data_row(hit)
    if not header:
        return {}
    idx = {h.strip().lower(): i for i, h in enumerate(header)}

    def g(name):
        return row[idx[name]].strip() if name in idx and idx[name] < len(row) else None

    return {"genus": g("genus"), "species": g("species"), "method": "taxmyPHAGE"}
