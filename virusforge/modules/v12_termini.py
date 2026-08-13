"""V12 — Genom Uçları / Termini (PhageTerm). Yalnız faj + paired-end kısa okuma.

PhageTerm paired-end kısa okuma gerektirir → LONG_READ/ASSEMBLY_INPUT modda N/A.
Çıktı format detayı gerçek PhageTerm koşusunda (T7 doğrulaması) teyit edilir; parser
kolon-adı tolerantı (class/type + left/right) olacak şekilde muhafazakâr yazıldı.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_phage, latest_genome, safe_run


def parse_phageterm(report_path) -> dict:
    """PhageTerm rapor CSV'si: termini sınıfı (DTR/cos/pac/headful) + uç pozisyonları."""
    lines = [ln for ln in Path(report_path).read_text().splitlines() if ln.strip()]
    if len(lines) < 2:
        return {}
    header = [h.strip() for h in lines[0].split(",")]
    row = [c.strip() for c in lines[1].split(",")]
    idx = {h.lower(): i for i, h in enumerate(header)}

    def pick(*needles):
        for i, h in enumerate(header):
            if any(n in h.lower() for n in needles) and i < len(row):
                return row[i]
        return None

    return {"termini_type": pick("class", "type"),
            "left": pick("left"), "right": pick("right"),
            "method": "PhageTerm"}


class V12Termini(Module):
    name = "Genome Termini"
    code = "V12"
    dirname = "V12_TERMINI"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not is_phage(ctx):
            m = {"note": "faj değil — termini analizi uygulanmaz"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)
        if ctx.mode not in ("SHORT_READ", "HYBRID"):
            m = {"note": f"PhageTerm paired-end kısa okuma gerektirir — mode={ctx.mode}"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        v01 = ctx.artifacts.get("V01", {})
        raw = util.find_short_reads(ctx.sample_dir)
        r1 = v01.get("clean_r1") or (str(raw[0]) if raw else None)
        r2 = v01.get("clean_r2") or (str(raw[1]) if raw else None)
        genome = latest_genome(ctx)
        if not (r1 and r2 and genome):
            m = {"note": "paired-end okuma veya genom yok — termini atlandı"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        work = dirs["02_work"]
        name = Path(ctx.sample_dir).name or "phageterm"
        err = safe_run(tools.phageterm_cmd(r1, r2, genome, name,
                                           conda_env=get(ctx.cfg, "tools.phageterm.conda_env", None),
                                           conda_bin=get(ctx.cfg, "tools.phageterm.conda_bin", "conda")),
                       dirs["07_logs"] / "phageterm.log")
        # PhageTerm çıktısını work/ (cwd yoksa) veya native içinde ara
        report = None
        for base in (work, dirs["03_native_outputs"], Path.cwd()):
            report = next(Path(base).glob("*[Rr]eport*.csv"), None)
            if report:
                break
        if not err and report:
            metrics = parse_phageterm(report)
            status = Status.PASS if metrics.get("termini_type") else Status.WARNING
        else:
            metrics = {"error": err or "PhageTerm çıktısı bulunamadı"}
            status = Status.WARNING
        (dirs["04_standardized"] / "termini.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
