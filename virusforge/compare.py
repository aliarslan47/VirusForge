"""Çoklu-örnek karşılaştırma: birden çok tamamlanmış koşuyu birlikte karşılaştır
(ortak filogenetik ağaç + örnekler-arası benzerlik matrisi + ICTV özet).

Per-örnek V-modülleri (V00–V10) dokunulmaz; bu ayrı bir komuttur (CLI `compare`).
Ağ gerektirmez (yerel MAFFT/IQ-TREE2/blastn).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import config, tools, util
from .config import get
from .module import safe_run
from .report.render import render_comparison


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


def _genome_length(fasta) -> int:
    return sum(len(l.strip()) for l in Path(fasta).read_text().splitlines() if not l.startswith(">"))


def _load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}


def collect_samples(run_dirs) -> list:
    """Her tamamlanmış run'dan genom + ad + ICTV (V09) + taksonomi (V04) + uzunluk topla.
    Genomu olmayan run atlanır."""
    samples = []
    for rd in run_dirs:
        rd = Path(rd)
        genome = rd / "V03_POLISHING_VIRAL_QC" / "04_standardized" / "viral_genome.fasta"
        if not genome.exists():
            continue
        v04 = next((rd / "V04_VIRAL_IDENTIFICATION" / "04_standardized").glob("*.json"), None)
        v09 = rd / "V09_COMPARATIVE_PHYLO" / "04_standardized" / "comparative.json"
        samples.append({
            "name": rd.name,
            "genome_path": str(genome),
            "length": _genome_length(genome),
            "taxonomy": (_load_json(v04).get("taxonomy") if v04 else "") or "",
            "ictv": (_load_json(v09).get("ictv") or {}) if v09.exists() else {},
        })
    return samples


def build_combined_fasta(samples, out_fasta) -> int:
    """Örnek genomlarını tek fasta'ya (header = örnek adı). Yazılan örnek sayısını döndür."""
    n = 0
    with open(out_fasta, "w") as out:
        for s in samples:
            seq = "".join(l.strip() for l in Path(s["genome_path"]).read_text().splitlines()
                          if not l.startswith(">"))
            if seq:
                out.write(f">{s['name']}\n{seq}\n")
                n += 1
    return n


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


def pairwise_identity_matrix(combined_fasta, work_dir, labels, threads=8):
    """makeblastdb + all-vs-all blastn → örnekler-arası % kimlik matrisi (yerel, ağsız)."""
    work = Path(work_dir)
    dbpfx = work / "cmpdb"
    if safe_run(tools.makeblastdb_nucl_cmd(combined_fasta, dbpfx), work / "makeblastdb.log"):
        return None
    bn = work / "allvall_blastn.tsv"
    if safe_run(tools.blastn_local_cmd(combined_fasta, dbpfx, bn, threads), work / "blastn.log"):
        return None
    if not bn.exists():
        return None
    return identity_matrix(labels, parse_blastn_identity(bn))


def _write_outputs(out, data):
    (out / "comparison.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    (out / "comparison_report.html").write_text(render_comparison(data))


def run_compare(run_dirs, out_dir, cfg=None):
    """Çoklu-örnek karşılaştırmayı koştur: ortak ağaç + benzerlik matrisi + rapor. out_dir döndürür."""
    cfg = cfg or config.load_config()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    samples = collect_samples(run_dirs)
    data = {"samples": samples}
    if len(samples) < 2:
        data["warning"] = "karşılaştırma için en az 2 geçerli genom gerekir"
        _write_outputs(out, data)
        return out

    threads = get(cfg, "general.threads", 8)
    combined = out / "combined.fasta"
    build_combined_fasta(samples, combined)
    labels = [s["name"] for s in samples]

    matrix = pairwise_identity_matrix(combined, out, labels, threads)
    if matrix:
        data["matrix_labels"] = labels
        data["matrix"] = matrix

    aln = out / "aln.fasta"
    try:
        util.run_redirect(tools.mafft_cmd(combined, aln), aln, out / "mafft.log")
    except RuntimeError:
        pass
    if aln.exists() and aln.stat().st_size > 0:
        pfx = out / "iqtree"
        if not safe_run(tools.iqtree_cmd(aln, pfx, threads, get(cfg, "tools.comparative.iqtree_bin", "iqtree")),
                        out / "iqtree.log"):
            tf = Path(str(pfx) + ".treefile")
            if tf.exists():
                data["tree_newick"] = tf.read_text().strip()

    _write_outputs(out, data)
    return out
