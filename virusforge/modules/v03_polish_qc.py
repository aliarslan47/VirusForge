"""V03 — Polishing (long) + Viral Genome Quality (QUAST + CheckV)."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_rna, safe_run


def parse_samtools_depth(depth_path, min_depth=1) -> dict:
    """`samtools depth -a` çıktısı (ref<TAB>pos<TAB>depth) → kapsama özeti (RNA referans-tabanlı QC).
    breadth_pct = derinlik≥min_depth pozisyon oranı; mean_depth = ortalama derinlik."""
    depths = []
    for line in Path(depth_path).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                depths.append(int(parts[2]))
            except ValueError:
                pass
    if not depths:
        return {"positions": 0, "covered_bases": 0, "breadth_pct": 0.0, "mean_depth": 0.0}
    covered = sum(1 for d in depths if d >= min_depth)
    return {"positions": len(depths), "covered_bases": covered,
            "breadth_pct": round(100 * covered / len(depths), 2),
            "mean_depth": round(sum(depths) / len(depths), 2)}


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


class V03PolishQC(Module):
    name = "Polishing & Viral Genome Quality"
    code = "V03"
    dirname = "V03_POLISHING_VIRAL_QC"

    def restore_artifacts(self, ctx: Context) -> None:
        genome = self.module_dir(ctx.run_dir) / "04_standardized" / "viral_genome.fasta"
        if genome.exists():
            ctx.artifacts[self.code] = {"genome": str(genome)}

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        threads = get(ctx.cfg, "general.threads", 8)
        draft = ctx.artifacts.get("V02", {}).get("draft")
        if not draft or not Path(draft).exists():
            m = {"error": "assembly draft bulunamadı"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        genome_src = Path(draft)
        problems: list[str] = []

        # yalnız saf LONG_READ'de Medaka cila. HYBRID'de Unicycler zaten short-okumayla
        # düzeltir; R9/Q10 ONT medaka'sı temiz hibrit assembly'ye hata GERİ sokar (T7'de CDS 76→55).
        long_reads = ctx.artifacts.get("V01", {}).get("clean_long")
        if ctx.mode == "LONG_READ" and long_reads:
            mout = dirs["02_work"] / "medaka"
            model = get(ctx.cfg, "tools.medaka.model", "auto")
            if model == "auto":
                # kimyaya-duyarlı model (Flye ile aynı R9/R10 kararı)
                from .v02_assembly import resolve_chemistry
                mq = (ctx.results.get("V01", {}).get("long") or {}).get("mean_qual")
                model = ("r941_min_sup_g507" if resolve_chemistry(mq) == "r9"
                         else "r1041_e82_400bps_sup_v5.0.0")
            err = safe_run(tools.medaka_consensus_cmd(
                long_reads, draft, mout, model, threads,
                conda_env=get(ctx.cfg, "tools.long.conda_env", None),
                conda_bin=get(ctx.cfg, "tools.long.conda_bin", "conda")),
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

        if is_rna(ctx):
            # RNA: CheckV faj/prokaryot-virüs odaklı → yerine referans BAM'inden kapsama (varsa).
            bam = ctx.artifacts.get("V02", {}).get("bam")
            if bam and Path(bam).exists():
                depth_tsv = dirs["02_work"] / "depth.tsv"
                min_d = get(ctx.cfg, "tools.rna.ivar_min_depth", 10)
                try:
                    util.run_redirect(tools.samtools_depth_cmd(
                        bam, get(ctx.cfg, "tools.rna.conda_env", None),
                        get(ctx.cfg, "tools.rna.conda_bin", "conda")), depth_tsv, dirs["07_logs"] / "depth.log")
                    cov = parse_samtools_depth(depth_tsv, min_d)
                    metrics["coverage"] = cov
                    if cov["breadth_pct"] < 90.0:
                        problems.append(f"düşük kapsama genişliği: {cov['breadth_pct']}% (@depth≥{min_d})")
                except RuntimeError:
                    problems.append("kapsama hesaplanamadı")
            # de novo RNA (BAM yok): CheckV atlanır, QUAST uzunluk/N50 yeterli
        else:
            # CheckV (DNA/faj)
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
