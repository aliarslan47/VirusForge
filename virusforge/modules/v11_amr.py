"""V11 — AMR + Virülans taraması (AMRFinderPlus). Yalnız fajlarda.

Boş sonuç (0 gen) geçerli bir PASS'tir — fajlarda AMR nadir; dürüstçe raporlanır.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_phage, latest_genome, safe_run

_TYPE_KEY = {"AMR": "amr", "VIRULENCE": "virulence", "STRESS": "stress"}


def parse_amrfinder(tsv_path) -> dict:
    """AMRFinderPlus TSV: Element type sütununa göre AMR/VIRULENCE/STRESS grupla."""
    lines = [ln for ln in Path(tsv_path).read_text().splitlines() if ln.strip()]
    out = {"amr_genes": [], "virulence_genes": [], "stress_genes": [],
           "counts": {"amr": 0, "virulence": 0, "stress": 0}}
    if len(lines) < 2:
        return out
    header = lines[0].split("\t")
    idx = {c.strip().lower(): i for i, c in enumerate(header)}

    def g(cols, *names):
        for n in names:
            if n in idx and idx[n] < len(cols):
                return cols[idx[n]].strip()
        return None

    for row in lines[1:]:
        cols = row.split("\t")
        etype = (g(cols, "element type") or "").upper()
        key = _TYPE_KEY.get(etype)
        if not key:
            continue
        gene = {
            "gene": g(cols, "gene symbol"),
            "name": g(cols, "sequence name"),
            "class": g(cols, "class"),
            "coverage": g(cols, "% coverage of reference sequence"),
            "identity": g(cols, "% identity to reference sequence"),
        }
        out[f"{key}_genes"].append(gene)
        out["counts"][key] += 1
    return out


class V11Amr(Module):
    name = "AMR & Virulence"
    code = "V11"
    dirname = "V11_AMR_VIRULENCE"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not is_phage(ctx):
            m = {"note": "faj değil — AMR taraması uygulanmaz"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        faa = ctx.artifacts.get("V07", {}).get("faa")
        if faa and Path(faa).exists():
            inp, is_protein = faa, True
        else:
            genome = latest_genome(ctx)
            if not genome:
                m = {"error": "AMRFinder için protein/genom bulunamadı"}
                return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)
            inp, is_protein = genome, False

        out_tsv = dirs["03_native_outputs"] / "amrfinder.tsv"
        db = get(ctx.cfg, "tools.amrfinder.db", "")
        err = safe_run(tools.amrfinder_cmd(inp, out_tsv, db, is_protein,
                                           get(ctx.cfg, "general.threads", 8),
                                           conda_env=get(ctx.cfg, "tools.amrfinder.conda_env", None),
                                           conda_bin=get(ctx.cfg, "tools.amrfinder.conda_bin", "conda")),
                       dirs["07_logs"] / "amrfinder.log")
        if not err and out_tsv.exists():
            metrics = parse_amrfinder(out_tsv)
            metrics["input_type"] = "protein" if is_protein else "nucleotide"
            status = Status.PASS          # boş liste dahil geçerli sonuç
        else:
            metrics = {"error": err or "AMRFinder çıktısı bulunamadı"}
            status = Status.WARNING
        (dirs["04_standardized"] / "amr_virulence.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
