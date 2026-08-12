"""V01 — Read QC & Preprocessing (short/long/hybrid)."""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, safe_run


def parse_fastp_json(path) -> dict:
    data = json.loads(Path(path).read_text())
    s = data.get("summary", {})
    before = s.get("before_filtering", {})
    after = s.get("after_filtering", {})
    return {
        "raw_reads": before.get("total_reads"),
        "clean_reads": after.get("total_reads"),
        "q30_rate": after.get("q30_rate"),
        "gc_content": after.get("gc_content"),
    }


def parse_nanoplot(nanostats_path) -> dict:
    wanted = {
        "Mean read length": "mean_len",
        "Read length N50": "read_n50",
        "Mean read quality": "mean_qual",
        "Number of reads": "number_of_reads",
    }
    out: dict = {}
    for line in Path(nanostats_path).read_text().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            key = wanted.get(k.strip())
            if key:
                out[key] = float(v.strip().replace(",", ""))
    return out


class V01ReadQC(Module):
    name = "Read QC & Preprocessing"
    code = "V01"
    dirname = "V01_READ_QC_PREPROCESSING"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        threads = get(ctx.cfg, "general.threads", 8)
        metrics: dict = {"mode": ctx.mode}
        artifacts: dict = {}
        problems: list[str] = []

        if ctx.mode == "ASSEMBLY_INPUT":
            m = {"note": "assembly girdisi — read QC yapılmaz"}
            self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m)
            return ModuleResult(Status.NOT_APPLICABLE, None, m)

        short = util.find_short_reads(ctx.sample_dir)
        long_r = util.find_long_reads(ctx.sample_dir)

        # --- short kol ---
        if ctx.mode in ("SHORT_READ", "HYBRID") and short:
            work = dirs["02_work"]
            cmd = tools.fastp_cmd(short[0], short[1], work, threads,
                                  get(ctx.cfg, "tools.fastp.extra_args", ""))
            err = safe_run(cmd, dirs["07_logs"] / "fastp.log")
            fj = work / "fastp.json"
            if err:
                problems.append(f"fastp: {err[:120]}")
            elif fj.exists():
                metrics["short"] = parse_fastp_json(fj)
                artifacts["clean_r1"] = str(work / "clean_R1.fastq.gz")
                artifacts["clean_r2"] = str(work / "clean_R2.fastq.gz")
            else:
                problems.append("fastp çıktısı (fastp.json) bulunamadı")

        # --- long kol ---
        if ctx.mode in ("LONG_READ", "HYBRID") and long_r:
            np_out = dirs["03_native_outputs"] / "nanoplot"
            np_out.mkdir(parents=True, exist_ok=True)
            err = safe_run(tools.nanoplot_cmd(long_r, np_out, threads),
                           dirs["07_logs"] / "nanoplot.log")
            stats = np_out / "NanoStats.txt"
            if not err and stats.exists():
                metrics["long"] = parse_nanoplot(stats)
            else:
                problems.append("NanoPlot çıktısı bulunamadı")
            # filtlong → temiz uzun okuma (.fastq, gz DEĞİL — BacForge dersi)
            clean_long = dirs["02_work"] / "clean_long.fastq"
            fl = tools.filtlong_cmd(long_r, get(ctx.cfg, "tools.filtlong.min_length", 1000),
                                    get(ctx.cfg, "tools.filtlong.keep_percent", 90))
            try:
                util.run_redirect(fl, clean_long, dirs["07_logs"] / "filtlong.log")
                if clean_long.stat().st_size > 0:
                    artifacts["clean_long"] = str(clean_long)
                else:
                    problems.append("filtlong boş çıktı verdi")
            except RuntimeError as exc:
                problems.append(f"filtlong: {str(exc)[:120]}")

        # MultiQC (varsa)
        safe_run(tools.multiqc_cmd(self.module_dir(ctx.run_dir), dirs["06_visualization"]),
                 dirs["07_logs"] / "multiqc.log")

        (dirs["04_standardized"] / "qc_metrics.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.artifacts[self.code] = artifacts
        ctx.results[self.code] = metrics

        status = Status.PASS if not problems else Status.WARNING
        if problems:
            metrics["problems"] = problems
        summary = self.write_summary(ctx.run_dir, status, metrics)
        return ModuleResult(status, summary, metrics)
