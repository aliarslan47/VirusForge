"""V12 — Soy/Klad Tayini (RNA yolu, Faz 3).

RNA virüs konsensüs genomundan soy hattı (Pangolin PANGO) + klad (Nextclade) tayini.
V02'nin ürettiği konsensüs FASTA (`ctx.artifacts["V02"]["draft"]`) üzerinden. İki araç bağımsız
çalışır (biri düşse diğeri devam, sessiz-hata yok). DNA/faj yolunda veya konsensüs yoksa N/A.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_rna, safe_run


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def parse_pangolin(csv_path) -> dict:
    """Pangolin lineage_report.csv → tek örnek satırı özeti. Boş/başlıksız → {}."""
    p = Path(csv_path)
    if not p.exists():
        return {}
    with open(p, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return {}
    r = rows[0]
    return {
        "lineage": (r.get("lineage") or "").strip(),
        "conflict": (r.get("conflict") or "").strip(),
        "scorpio_call": (r.get("scorpio_call") or "").strip(),
        "qc_status": (r.get("qc_status") or "").strip(),
        "note": (r.get("note") or "").strip(),
        "version": (r.get("version") or "").strip(),
        "pango_version": (r.get("pangolin_version") or "").strip(),
    }


def parse_nextclade(tsv_path) -> dict:
    """Nextclade TSV → tek örnek satırı özeti. Veri satırı yoksa → {}."""
    p = Path(tsv_path)
    if not p.exists():
        return {}
    with open(p, newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        return {}
    r = rows[0]
    return {
        "clade": (r.get("clade") or "").strip(),
        "nextclade_pango": (r.get("Nextclade_pango") or "").strip(),
        "qc_overall": (r.get("qc.overallStatus") or "").strip(),
        "total_substitutions": _int(r.get("totalSubstitutions")),
        "total_missing": _int(r.get("totalMissing")),
        "total_aa_substitutions": _int(r.get("totalAminoacidSubstitutions")),
    }


class V12Lineage(Module):
    code = "V12"
    name = "Soy/Klad Tayini"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not is_rna(ctx):
            m = {"note": "DNA/faj yolu — soy/klad tayini uygulanmadı"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)
        v02 = ctx.artifacts.get("V02", {}) or {}
        cons = v02.get("draft")
        if not cons or not Path(cons).exists():
            m = {"note": "konsensüs genom yok (de novo/referanssız) — soy tayini yapılamaz"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        metrics: dict = {}
        problems: list[str] = []
        native = dirs["03_native_outputs"]

        # Pangolin (izole vf_pangolin env)
        pcsv = native / "lineage_report.csv"
        err = safe_run(tools.pangolin_cmd(cons, pcsv,
                                          get(ctx.cfg, "tools.pangolin.threads", 4),
                                          get(ctx.cfg, "tools.pangolin.conda_env", None),
                                          get(ctx.cfg, "tools.pangolin.conda_bin", "conda")),
                       dirs["07_logs"] / "pangolin.log")
        pang = parse_pangolin(pcsv)
        if pang:
            metrics["pangolin"] = pang
        elif err:
            problems.append(f"Pangolin: {err[:120]}")
        else:
            problems.append("Pangolin: soy atanmadı")

        # Nextclade (izole vf_nextclade env)
        dataset_dir = get(ctx.cfg, "tools.nextclade.dataset_dir", "")
        if not dataset_dir or not Path(dataset_dir).exists():
            problems.append(f"Nextclade: dataset dizini yok ({dataset_dir}); "
                            "`nextclade dataset get` ile indir")
        else:
            ntsv = native / "nextclade.tsv"
            err = safe_run(tools.nextclade_run_cmd(cons, dataset_dir, ntsv,
                                                   get(ctx.cfg, "tools.nextclade.conda_env", None),
                                                   get(ctx.cfg, "tools.nextclade.conda_bin", "conda")),
                           dirs["07_logs"] / "nextclade.log")
            nc = parse_nextclade(ntsv)
            if nc:
                metrics["nextclade"] = nc
            elif err:
                problems.append(f"Nextclade: {err[:120]}")
            else:
                problems.append("Nextclade: klad atanmadı")

        if "pangolin" not in metrics and "nextclade" not in metrics:
            metrics["error"] = "; ".join(problems) or "soy/klad üretilmedi"
            return ModuleResult(Status.WARNING,
                                self.write_summary(ctx.run_dir, Status.WARNING, metrics), metrics)
        if problems:
            metrics["problems"] = problems
        (dirs["04_standardized"] / "lineage.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        status = Status.PASS if not problems else Status.WARNING
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
