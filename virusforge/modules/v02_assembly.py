"""V02 — Viral Genome Assembly (SPAdes/Flye/Unicycler yönlendirme)."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, safe_run


# Flye --nano-hq (R10) yalnız düşük-hatalı okumalar için; yüksek-hatalı (R9-tipi)
# veride çöker ("No disjointigs assembled"). Ortalama okuma kalitesiyle otomatik seç.
_HQ_QUAL_THRESHOLD = 13.0   # ~ Q13 (<%5 hata) altı → R9 (--nano-raw)


def resolve_chemistry(mean_qual) -> str:
    """NanoPlot ortalama kalitesinden ONT kimyası: düşük kalite→r9, yüksek→r10.
    Bilinmiyorsa modern varsayılan r10 (gerçek T7 doğrulamasında bulundu)."""
    if mean_qual is None:
        return "r10"
    return "r10" if float(mean_qual) >= _HQ_QUAL_THRESHOLD else "r9"


def select_assembler(mode: str, reads: dict, out_dir, cfg: dict, mean_qual=None):
    """(cmd, üretilecek contig dosyası) döndür. Gerekli okuma yoksa ValueError (sessiz PASS yasak)."""
    threads = get(cfg, "general.threads", 8)
    lenv = get(cfg, "tools.long.conda_env", None)
    lbin = get(cfg, "tools.long.conda_bin", "conda")
    out = Path(out_dir)
    if mode == "SHORT_READ":
        if not (reads.get("r1") and reads.get("r2")):
            raise ValueError("SHORT_READ için R1/R2 bulunamadı")
        return tools.spades_cmd(reads["r1"], reads["r2"], out, threads,
                                get(cfg, "tools.spades.careful", True)), out / "contigs.fasta"
    if mode == "LONG_READ":
        if not reads.get("long"):
            raise ValueError("LONG_READ için uzun-okuma bulunamadı")
        chem = get(cfg, "tools.flye.chemistry", "auto")
        if str(chem).lower() == "auto":
            chem = resolve_chemistry(mean_qual)   # kaliteye-dayalı R9/R10 (Q<13 → --nano-raw)
        return tools.flye_cmd(reads["long"], out, chem, threads,
                              conda_env=lenv, conda_bin=lbin), out / "assembly.fasta"
    if mode == "HYBRID":
        if not (reads.get("r1") and reads.get("r2") and reads.get("long")):
            raise ValueError("HYBRID için short+long birlikte gerekli")
        return tools.unicycler_cmd(reads["r1"], reads["r2"], reads["long"], out, threads,
                                   conda_env=lenv, conda_bin=lbin), out / "assembly.fasta"
    raise ValueError(f"assembly bu modda çalışmaz: {mode}")


class V02Assembly(Module):
    name = "Viral Genome Assembly"
    code = "V02"
    dirname = "V02_VIRAL_ASSEMBLY"

    def restore_artifacts(self, ctx: Context) -> None:
        draft = self.module_dir(ctx.run_dir) / "04_standardized" / "draft_viral_genome.fasta"
        if draft.exists():
            ctx.artifacts[self.code] = {"draft": str(draft)}

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if ctx.mode == "ASSEMBLY_INPUT":
            # hazır assembly'yi doğrudan draft yap
            fa = next((p for p in Path(ctx.sample_dir).iterdir()
                       if p.name.lower().endswith((".fasta", ".fa", ".fna"))), None)
            if fa:
                draft = dirs["04_standardized"] / "draft_viral_genome.fasta"
                shutil.copy(fa, draft)
                ctx.artifacts[self.code] = {"draft": str(draft)}
                m = {"source": "assembly_input", "draft": str(draft)}
                return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, m), m)

        v01 = ctx.artifacts.get("V01", {})
        raw_short = util.find_short_reads(ctx.sample_dir)
        raw_long = util.find_long_reads(ctx.sample_dir)
        reads = {
            "r1": v01.get("clean_r1") or (str(raw_short[0]) if raw_short else None),
            "r2": v01.get("clean_r2") or (str(raw_short[1]) if raw_short else None),
            "long": v01.get("clean_long") or (str(raw_long) if raw_long else None),
        }
        work = dirs["02_work"] / "asm"
        mean_qual = (ctx.results.get("V01", {}).get("long") or {}).get("mean_qual")
        try:
            cmd, contig = select_assembler(ctx.mode, reads, work, ctx.cfg, mean_qual=mean_qual)
        except ValueError as exc:
            m = {"error": str(exc)}
            return ModuleResult(Status.FAIL, self.write_summary(ctx.run_dir, Status.FAIL, m), m)

        err = safe_run(cmd, dirs["07_logs"] / "assembly.log")
        if err or not Path(contig).exists():
            m = {"assembler_cmd": cmd[0], "error": err or f"contig üretilmedi: {contig}"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        draft = dirs["04_standardized"] / "draft_viral_genome.fasta"
        shutil.copy(contig, draft)
        ctx.artifacts[self.code] = {"draft": str(draft)}
        m = {"assembler": cmd[0], "draft": str(draft)}
        ctx.results[self.code] = m
        return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, m), m)
