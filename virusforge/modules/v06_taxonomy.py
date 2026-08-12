"""V06 — Taxonomy & Closest References (Mash vs INPHARED)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, latest_genome

_ACC = re.compile(r"(GCF_\d+\.\d+|GCA_\d+\.\d+|[A-Z]{1,2}\d{5,8}\.\d+)")


def _accession(ref_path: str) -> str:
    m = _ACC.search(ref_path)
    return m.group(1) if m else Path(ref_path).stem


def parse_mash(dist_tsv, top: int = 10) -> list[dict]:
    """Mash dist çıktısını mesafeye göre sırala, ACCESSION'a göre DEDUP (BacForge dersi)."""
    rows = []
    for line in Path(dist_tsv).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        ref, _query, dist = parts[0], parts[1], parts[2]
        try:
            d = float(dist)
        except ValueError:
            continue
        rows.append({"accession": _accession(ref), "reference": ref, "mash_dist": d})
    rows.sort(key=lambda r: r["mash_dist"])
    seen, out = set(), []
    for r in rows:
        if r["accession"] in seen:
            continue
        seen.add(r["accession"])
        out.append(r)
        if len(out) >= top:
            break
    return out


class V06Taxonomy(Module):
    name = "Taxonomy & Closest References"
    code = "V06"
    dirname = "V06_TAXONOMY_CLOSEST_REFERENCES"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        genome = latest_genome(ctx)
        sketch = get(ctx.cfg, "tools.mash.inphared_sketch", "databases/inphared/inphared.msh")
        if not genome or not Path(sketch).exists():
            m = {"error": "genom veya INPHARED sketch bulunamadı", "sketch": str(sketch)}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        dist = dirs["03_native_outputs"] / "mash_dist.tsv"
        try:
            util.run_redirect(tools.mash_dist_cmd(sketch, genome), dist,
                              dirs["07_logs"] / "mash.log")
        except RuntimeError as exc:
            m = {"error": str(exc)[:200]}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        closest = parse_mash(dist)
        result = {"closest_10": closest, "n_hits": len(closest)}
        (dirs["04_standardized"] / "closest_references.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False))
        ctx.results[self.code] = result
        status = Status.PASS if closest else Status.WARNING
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, result), result)
