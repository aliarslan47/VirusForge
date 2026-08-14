"""V11 — Soy/Klad Tayini (RNA yolu, Faz 3).

RNA virüs konsensüs genomundan klad + PANGO soyu (Nextclade) tayini. V02'nin ürettiği konsensüs
FASTA (`ctx.artifacts["V02"]["draft"]`) üzerinden. DNA/faj yolunda veya konsensüs yoksa N/A.
Not: Nextclade `Nextclade_pango` alanı PANGO soyunu zaten verdiği için ayrı Pangolin kullanılmaz.
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


class V11Lineage(Module):
    code = "V11"
    name = "Soy/Klad Tayini"
    dirname = "V11_LINEAGE"

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

        # Nextclade (izole vf_nextclade env) — klad + PANGO soyu + QC + mutasyon
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

        if "nextclade" not in metrics:
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
