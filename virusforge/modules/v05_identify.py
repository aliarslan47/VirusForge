"""V05 — Viral Sequence Identification (geNomad)."""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, latest_genome, safe_run


def parse_genomad(virus_summary_tsv) -> dict:
    lines = Path(virus_summary_tsv).read_text().splitlines()
    if len(lines) < 2:
        return {"is_viral": False, "n_viral": 0, "top_score": None, "taxonomy": None}
    header = lines[0].split("\t")
    idx = {c: i for i, c in enumerate(header)}
    best_score, tax = None, None
    for row in lines[1:]:
        cols = row.split("\t")
        if "virus_score" in idx and idx["virus_score"] < len(cols):
            try:
                sc = float(cols[idx["virus_score"]])
            except ValueError:
                continue
            if best_score is None or sc > best_score:
                best_score = sc
                tax = cols[idx["taxonomy"]] if "taxonomy" in idx and idx["taxonomy"] < len(cols) else None
    return {"is_viral": len(lines) - 1 > 0, "n_viral": len(lines) - 1,
            "top_score": best_score, "taxonomy": tax}


class V05Identify(Module):
    name = "Viral Sequence Identification"
    code = "V05"
    dirname = "V05_VIRAL_IDENTIFICATION"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        genome = latest_genome(ctx)
        if not genome:
            m = {"error": "girdi genom bulunamadı"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        db = get(ctx.cfg, "tools.genomad.db", "databases/genomad")
        out = dirs["03_native_outputs"] / "genomad"
        err = safe_run(tools.genomad_cmd(genome, out, db, get(ctx.cfg, "general.threads", 8)),
                       dirs["07_logs"] / "genomad.log")
        # geNomad çıktısı: <stem>_summary/<stem>_virus_summary.tsv
        stem = Path(genome).stem
        vs = out / f"{stem}_summary" / f"{stem}_virus_summary.tsv"
        result: dict = {"tools": {}}
        if not err and vs.exists():
            g = parse_genomad(vs)
            result["tools"]["genomad"] = g
            result.update(g)  # üst düzey konsensüs = geNomad (tek araç M1)
            status = Status.PASS
        else:
            result["error"] = err or "geNomad çıktısı bulunamadı"
            status = Status.WARNING
        # (opsiyonel VirSorter2/VIBRANT açıksa buraya eklenir; uyuşmazlık gizlenmez)
        (dirs["04_standardized"] / "viral_identification.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False))
        ctx.results[self.code] = result
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, result), result)
