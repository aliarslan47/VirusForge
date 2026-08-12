"""V03 — Viral Genome Assembly (SPAdes/Flye/Unicycler yönlendirme)."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, safe_run


def select_assembler(mode: str, reads: dict, out_dir, cfg: dict):
    """(cmd, üretilecek contig dosyası) döndür. Gerekli okuma yoksa ValueError (sessiz PASS yasak)."""
    threads = get(cfg, "general.threads", 8)
    out = Path(out_dir)
    if mode == "SHORT_READ":
        if not (reads.get("r1") and reads.get("r2")):
            raise ValueError("SHORT_READ için R1/R2 bulunamadı")
        return tools.spades_cmd(reads["r1"], reads["r2"], out, threads,
                                get(cfg, "tools.spades.careful", True)), out / "contigs.fasta"
    if mode == "LONG_READ":
        if not reads.get("long"):
            raise ValueError("LONG_READ için uzun-okuma bulunamadı")
        chem = get(cfg, "tools.flye.chemistry", "r10")
        return tools.flye_cmd(reads["long"], out, chem, threads), out / "assembly.fasta"
    if mode == "HYBRID":
        if not (reads.get("r1") and reads.get("r2") and reads.get("long")):
            raise ValueError("HYBRID için short+long birlikte gerekli")
        return tools.unicycler_cmd(reads["r1"], reads["r2"], reads["long"], out, threads), out / "assembly.fasta"
    raise ValueError(f"assembly bu modda çalışmaz: {mode}")


class V03Assembly(Module):
    name = "Viral Genome Assembly"
    code = "V03"
    dirname = "V03_VIRAL_ASSEMBLY"

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
        try:
            cmd, contig = select_assembler(ctx.mode, reads, work, ctx.cfg)
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
