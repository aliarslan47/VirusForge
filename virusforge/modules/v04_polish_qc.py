"""V04 — Polishing (long) + Viral Genome Quality (QUAST + CheckV)."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, safe_run


def parse_quast(report_tsv) -> dict:
    want = {"Total length": "total_length", "# contigs": "contigs",
            "N50": "n50", "GC (%)": "gc", "Largest contig": "largest_contig"}
    out: dict = {}
    for line in Path(report_tsv).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] in want:
            val = parts[1].strip()
            try:
                out[want[parts[0]]] = float(val) if "." in val else int(val)
            except ValueError:
                out[want[parts[0]]] = val
    return out


def parse_checkv(quality_summary_tsv) -> dict:
    lines = Path(quality_summary_tsv).read_text().splitlines()
    if len(lines) < 2:
        return {}
    header = lines[0].split("\t")
    idx = {c: i for i, c in enumerate(header)}
    best = None
    for row in lines[1:]:
        cols = row.split("\t")
        length = int(cols[idx["contig_length"]]) if "contig_length" in idx else 0
        if best is None or length > best[0]:
            best = (length, cols)
    if not best:
        return {}
    cols = best[1]

    def g(name):
        return cols[idx[name]] if name in idx and idx[name] < len(cols) else None
    return {
        "contig_length": best[0],
        "completeness": g("completeness"),
        "contamination": g("contamination"),
        "checkv_quality": g("checkv_quality"),
    }


class V04PolishQC(Module):
    name = "Polishing & Viral Genome Quality"
    code = "V04"
    dirname = "V04_POLISHING_VIRAL_QC"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        threads = get(ctx.cfg, "general.threads", 8)
        draft = ctx.artifacts.get("V03", {}).get("draft")
        if not draft or not Path(draft).exists():
            m = {"error": "assembly draft bulunamadı"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        genome_src = Path(draft)
        problems: list[str] = []

        # long ise Medaka cila
        long_reads = ctx.artifacts.get("V01", {}).get("clean_long")
        if ctx.mode in ("LONG_READ", "HYBRID") and long_reads:
            mout = dirs["02_work"] / "medaka"
            model = get(ctx.cfg, "tools.medaka.model", "auto")
            model = "r1041_e82_400bps_sup_v5.0.0" if model == "auto" else model
            err = safe_run(tools.medaka_consensus_cmd(long_reads, draft, mout, model, threads),
                           dirs["07_logs"] / "medaka.log")
            polished = mout / "consensus.fasta"
            if not err and polished.exists():
                genome_src = polished
            else:
                problems.append("Medaka cilası tamamlanamadı (draft kullanılıyor)")

        genome = dirs["04_standardized"] / "viral_genome.fasta"
        shutil.copy(genome_src, genome)
        ctx.artifacts[self.code] = {"genome": str(genome)}

        metrics: dict = {"polishing_performed": genome_src != Path(draft)}

        # QUAST
        qout = dirs["03_native_outputs"] / "quast"
        err = safe_run(tools.quast_cmd(genome, qout, threads), dirs["07_logs"] / "quast.log")
        qrep = qout / "report.tsv"
        if not err and qrep.exists():
            metrics["quast"] = parse_quast(qrep)
        else:
            problems.append("QUAST çıktısı bulunamadı")

        # CheckV
        cout = dirs["03_native_outputs"] / "checkv"
        db = get(ctx.cfg, "tools.checkv.db", "databases/checkv")
        err = safe_run(tools.checkv_cmd(genome, cout, db, threads), dirs["07_logs"] / "checkv.log")
        cqs = cout / "quality_summary.tsv"
        if not err and cqs.exists():
            metrics["checkv"] = parse_checkv(cqs)
        else:
            problems.append("CheckV değeri yok")

        (dirs["04_standardized"] / "genome_quality.json").write_text(
            __import__("json").dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        status = Status.PASS if not problems else Status.WARNING
        if problems:
            metrics["problems"] = problems
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
