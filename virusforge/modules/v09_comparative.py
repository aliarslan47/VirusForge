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


def _v05_fallback_hits(ctx, n) -> list[dict]:
    """Online BLAST erişilemezse: V05'in yerel Mash+INPHARED en yakın akrabalarını referans yap."""
    closest = (ctx.results.get("V05", {}) or {}).get("closest_10") or []
    return [{"accession": c["accession"], "species": c["accession"],
             "identity": None, "coverage": None} for c in closest[:n] if c.get("accession")]


def _read_seq(fasta) -> str:
    return "".join(l.strip() for l in Path(fasta).read_text().splitlines() if not l.startswith(">"))


def _wrap(cmd, cenv, cbin):
    return [cbin, "run", "-n", cenv, *cmd] if cenv else cmd


def _fetch_genomes(hits, cache_dir, cenv, cbin, logs):
    """Her hit accession'ını efetch ile çek (cache). Çekilebilen fasta yollarını döndür."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    fetched = []
    for h in hits:
        acc = h["accession"]
        fa = cache / f"{acc}.fasta"
        if not fa.exists() or fa.stat().st_size == 0:
            try:
                util.run_redirect(_wrap(tools.efetch_cmd(acc, fa), cenv, cbin), fa, logs / f"efetch_{acc}.log")
            except RuntimeError:
                continue
        if fa.exists() and fa.stat().st_size > 0:
            fetched.append(fa)
    return fetched


class V09Comparative(Module):
    name = "Comparative Identification & Phylogeny"
    code = "V09"
    dirname = "V09_COMPARATIVE_PHYLO"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not (ctx.results.get("V04", {}) or {}).get("is_viral"):
            m = {"note": "viral değil — karşılaştırma uygulanmadı"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)
        genome = latest_genome(ctx)
        if not genome:
            m = {"error": "girdi genom yok"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        cfg = ctx.cfg
        cenv = get(cfg, "tools.comparative.conda_env", None) or None
        cbin = get(cfg, "tools.comparative.conda_bin", "conda")
        n = get(cfg, "tools.comparative.n_closest", 5)
        metrics: dict = {}

        min_hits = get(cfg, "tools.comparative.min_hits", 3)

        # (1) online BLAST → en yakın türler (birincil, tanımlama)
        blast_tsv = dirs["03_native_outputs"] / "blast.tsv"
        bcmd = _wrap(tools.blastn_remote_cmd(genome, blast_tsv,
                     get(cfg, "tools.comparative.blast_db", "ref_viruses_rep_genomes")), cenv, cbin)
        err = safe_run(bcmd, dirs["07_logs"] / "blast.log")
        hits = parse_blast_hits(blast_tsv, n) if (not err and blast_tsv.exists()) else []
        if hits:
            metrics["blast_top_hit"] = hits[0]
            metrics["closest_species"] = hits
            metrics["ref_source"] = "blast_online"

        # (1b) fallback: online BLAST erişilemezse V05 (yerel Mash+INPHARED) akrabaları
        if len(hits) < min_hits:
            fb = _v05_fallback_hits(ctx, n)
            if len(fb) >= min_hits:
                hits = fb
                metrics["ref_source"] = "v05_mash_fallback"
                metrics["blast_note"] = err or "online BLAST erişilemedi → V05 en yakın akrabaları kullanıldı"

        # (2) taxmyPHAGE → ICTV cins/tür (BLAST'tan BAĞIMSIZ; yerel VIRIDIC)
        tout = dirs["03_native_outputs"] / "taxmyphage"
        if not safe_run(_wrap(tools.taxmyphage_cmd(genome, tout, get(cfg, "general.threads", 8)), cenv, cbin),
                        dirs["07_logs"] / "taxmyphage.log") and tout.exists():
            metrics["ictv"] = parse_taxmyphage(tout)

        # (3) yeterli referans varsa: efetch → MAFFT → IQ-TREE2 ağaç
        if len(hits) >= min_hits:
            combined = dirs["02_work"] / "sample_plus_refs.fasta"
            with open(combined, "w") as out:
                out.write(f">sample\n{_read_seq(genome)}\n")
            refs = _fetch_genomes(hits, get(cfg, "tools.comparative.ref_cache", "databases/ref_cache"),
                                  cenv, cbin, dirs["07_logs"])
            for fa in refs:
                with open(combined, "a") as out:
                    out.write(Path(fa).read_text())
            aln = dirs["02_work"] / "aln.fasta"
            try:
                util.run_redirect(_wrap(tools.mafft_cmd(combined, aln), cenv, cbin), aln, dirs["07_logs"] / "mafft.log")
            except RuntimeError:
                pass
            if aln.exists() and aln.stat().st_size > 0:
                pfx = dirs["03_native_outputs"] / "iqtree"
                iq = tools.iqtree_cmd(aln, pfx, get(cfg, "general.threads", 8),
                                      get(cfg, "tools.comparative.iqtree_bin", "iqtree"))
                if not safe_run(_wrap(iq, cenv, cbin), dirs["07_logs"] / "iqtree.log"):
                    tf = Path(str(pfx) + ".treefile")
                    if tf.exists():
                        metrics["tree"] = parse_iqtree(tf)
        else:
            metrics.setdefault("error", "yeterli akraba yok (online BLAST + V05 fallback) — ağaç atlandı")

        (dirs["04_standardized"] / "comparative.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        status = Status.PASS if (metrics.get("tree") or metrics.get("ictv")) else Status.WARNING
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
