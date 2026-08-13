"""V13 — Yapısal / Domain Annotation (phold). Yalnız fajlarda.

phold, pharokka (V07) GenBank'ini alıp ProstT5/Foldseek ile yapı-tabanlı fonksiyon
atar → pharokka'nın "unknown function" CDS'lerinin bir kısmını fonksiyona çevirir.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_phage, safe_run

_NON_FUNC = {"cds", "trnas", "trna", "crisprs", "tmrnas", "unknown function"}


def parse_phold(cds_functions_tsv) -> dict:
    """phold_all_cds_functions.tsv (pharokka formatı): kategorileri contig'ler üzerinden topla."""
    counts: dict = {}
    for line in Path(cds_functions_tsv).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            key, val = parts[0].strip(), parts[1].strip()
            if key.lower() in ("description", ""):
                continue
            try:
                counts[key] = counts.get(key, 0) + int(val)
            except ValueError:
                pass
    unknown = 0
    for k, v in counts.items():
        if k.lower() == "unknown function":
            unknown = v
    annotated = sum(v for k, v in counts.items()
                    if k.lower() not in _NON_FUNC and isinstance(v, int))
    return {"cds": counts.get("CDS"), "unknown_function": unknown,
            "annotated_cds": annotated, "functions": counts}


class V13Domain(Module):
    name = "Structural / Domain Annotation"
    code = "V13"
    dirname = "V13_DOMAIN_ANNOTATION"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not is_phage(ctx):
            m = {"note": "faj değil — domain annotation uygulanmaz"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        gbk = ctx.artifacts.get("V07", {}).get("gbk")
        if not gbk or not Path(gbk).exists():
            m = {"error": "pharokka GenBank (V07) bulunamadı — phold çalışamaz"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        out = dirs["03_native_outputs"] / "phold"
        db = get(ctx.cfg, "tools.phold.db", "")
        err = safe_run(tools.phold_cmd(gbk, out, db, get(ctx.cfg, "general.threads", 8),
                                       conda_env=get(ctx.cfg, "tools.phold.conda_env", None),
                                       conda_bin=get(ctx.cfg, "tools.phold.conda_bin", "conda")),
                       dirs["07_logs"] / "phold.log")
        cds_fn = next(out.glob("*_all_cds_functions.tsv"), None) if out.exists() else None
        if not err and cds_fn:
            metrics = parse_phold(cds_fn)
            # pharokka (V07) ile karşılaştır: unknown azaldı mı?
            v07 = ctx.results.get("V07", {})
            metrics["unknown_before"] = (v07.get("functions") or {}).get("unknown function")
            metrics["unknown_after"] = metrics.get("unknown_function")
            status = Status.PASS
            for png in out.glob("*.png"):
                shutil.copy(png, dirs["06_visualization"] / png.name)
        else:
            metrics = {"error": err or "phold çıktısı bulunamadı"}
            status = Status.WARNING
        (dirs["04_standardized"] / "domain_annotation.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
