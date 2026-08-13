"""V09 — Host/Konak Tahmini (RaFAH varsayılan · iPHoP opsiyonel). Yalnız fajlarda."""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_phage, latest_genome, safe_run


def _first_data_row(path, sep):
    lines = [ln for ln in Path(path).read_text().splitlines() if ln.strip()]
    if len(lines) < 2:
        return None, None
    return lines[0].split(sep), lines[1].split(sep)


def _pick(header, row, *needles, exclude=()):
    """Header'da needle içeren ilk sütunun değerini döndür (tolerant kolon eşleme)."""
    for i, h in enumerate(header):
        hl = h.lower()
        if any(n in hl for n in needles) and not any(x in hl for x in exclude) and i < len(row):
            return row[i].strip()
    return None


def parse_rafah(tsv_path) -> dict:
    """RaFAH *_Host_Predictions.tsv: tahmin edilen host + skor (tolerant kolon)."""
    header, row = _first_data_row(tsv_path, "\t")
    if not header:
        return {}
    return {"predicted_host": _pick(header, row, "host", exclude=("score",)),
            "confidence": _pick(header, row, "score", "confidence"),
            "raw_row": dict(zip(header, row))}


def parse_iphop(csv_path) -> dict:
    """iPHoP Host_prediction_to_genus_*.csv: host cinsi + güven skoru."""
    header, row = _first_data_row(csv_path, ",")
    if not header:
        return {}
    return {"predicted_host": _pick(header, row, "host"),
            "confidence": _pick(header, row, "confidence", "score"),
            "raw_row": dict(zip(header, row))}


class V09Host(Module):
    name = "Host Prediction"
    code = "V09"
    dirname = "V09_HOST_PREDICTION"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not is_phage(ctx):
            m = {"note": "faj değil — konak tahmini uygulanmaz"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)
        genome = latest_genome(ctx)
        if not genome:
            m = {"error": "girdi genom bulunamadı"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        method = get(ctx.cfg, "tools.host.method", "rafah").lower()
        cenv = get(ctx.cfg, "tools.host.conda_env", None)
        cbin = get(ctx.cfg, "tools.host.conda_bin", "conda")
        native = dirs["03_native_outputs"]
        metrics: dict = {"method": method}
        if method == "iphop":
            out = native / "iphop"
            db = get(ctx.cfg, "tools.host.iphop_db", "databases/iphop")
            err = safe_run(tools.iphop_cmd(genome, out, db, get(ctx.cfg, "general.threads", 8),
                                           conda_env=cenv, conda_bin=cbin),
                           dirs["07_logs"] / "iphop.log")
            hit = next(out.glob("Host_prediction_to_genus_*.csv"), None) if out.exists() else None
            parsed = parse_iphop(hit) if (not err and hit) else {}
        else:  # rafah
            prefix = native / "rafah"
            err = safe_run(tools.rafah_cmd(genome, prefix, conda_env=cenv, conda_bin=cbin),
                           dirs["07_logs"] / "rafah.log")
            hit = next(native.glob("*Host_Prediction*.tsv"), None)
            parsed = parse_rafah(hit) if (not err and hit) else {}

        if parsed and parsed.get("predicted_host"):
            metrics.update(parsed)
            status = Status.PASS
        else:
            metrics["error"] = err or f"{method} çıktısı bulunamadı"
            status = Status.WARNING
        (dirs["04_standardized"] / "host_prediction.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
