"""V08 — Phage-Specific Characterization (PhaBOX). Yalnız bakteriyofajlarda."""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, latest_genome, safe_run


def parse_phabox(final_dir) -> dict:
    """PhaBOX end_to_end sonuçları: phatyp (lifestyle) + phagcn (taxonomy) + phamer."""
    d = Path(final_dir)
    out: dict = {}

    def _first_data_row(tsv):
        lines = Path(tsv).read_text().splitlines()
        if len(lines) < 2:
            return None, None
        return lines[0].split("\t"), lines[1].split("\t")

    for fname, key in (("phatyp_prediction.tsv", "lifestyle"),
                       ("phagcn_prediction.tsv", "taxonomy"),
                       ("phamer_prediction.tsv", "phamer")):
        p = d / fname
        if p.exists():
            header, row = _first_data_row(p)
            if header and row:
                out[key] = dict(zip(header, row))
    return out


class V08PhageChar(Module):
    name = "Phage-Specific Characterization"
    code = "V08"
    dirname = "V08_PHAGE_CHARACTERIZATION"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        # V05 faj demiyorsa N/A (genel viral hat devam eder, bu modül atlanır)
        v05 = ctx.results.get("V05", {})
        tax = (v05.get("taxonomy") or "").lower()
        if v05 and v05.get("is_viral") and tax and "caudo" not in tax and "phage" not in tax and "virus" in tax:
            # viral ama faj değil görünüyor → N/A (yine de PhaBOX phamer ile teyit edebilir; muhafazakar)
            pass
        genome = latest_genome(ctx)
        if not genome:
            m = {"note": "girdi genom yok"}
            return ModuleResult(Status.NOT_APPLICABLE, self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        db = get(ctx.cfg, "tools.phabox.db", "databases/phabox")
        out = dirs["03_native_outputs"] / "phabox"
        err = safe_run(tools.phabox_cmd(genome, out, db, get(ctx.cfg, "general.threads", 8)),
                       dirs["07_logs"] / "phabox.log")
        final_dir = out / "final_prediction"
        if not err and final_dir.exists():
            metrics = parse_phabox(final_dir)
            status = Status.PASS if metrics else Status.WARNING
        else:
            metrics = {"error": err or "PhaBOX çıktısı bulunamadı"}
            status = Status.WARNING
        (dirs["04_standardized"] / "phage_characterization.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
