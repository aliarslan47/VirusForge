"""V10 — Final Report & Export."""
from __future__ import annotations

import json
from pathlib import Path

from ..module import Context, Module, ModuleResult, Status
from ..report.render import render_html

# Rapor sırası (M1 çekirdek + M2-A faj zenginleştirme: V08 AMR)
_ORDER = ["V00", "V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09"]


class V10Report(Module):
    name = "Final Report & Export"
    code = "V10"
    dirname = "V10_REPORT_EXPORT"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        run_dir = Path(ctx.run_dir)

        # tüm Vxx_summary.json'ları topla
        summaries: dict[str, dict] = {}
        for sub in run_dir.iterdir():
            if not sub.is_dir():
                continue
            for f in sub.glob("V*_summary.json"):
                data = json.loads(f.read_text())
                summaries[data.get("code", f.stem)] = data

        modules = []
        provenance = []
        for code in _ORDER:
            data = summaries.get(code)
            if data is None:
                # analiz koşmadıysa bölüm yine de görünür (bulgu yok ≠ sil)
                modules.append({"code": code, "module": "", "status": "SKIPPED",
                                "metrics": {"note": "modül koşmadı"}})
                continue
            modules.append(data)
            provenance.extend(data.get("provenance", []))

        # V10 kendini de PASS olarak ekle (rapor kendi summary'sinden önce üretiliyor)
        modules.append({"code": "V10", "module": self.name, "status": "PASS",
                        "metrics": {"note": "rapor + provenance üretildi"}})
        report = {
            "sample": Path(ctx.sample_dir).name,
            "mode": ctx.mode,
            "run_id": run_dir.name,
            "modules": modules,
        }
        (dirs["04_standardized"] / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False))
        (run_dir / "report.html").write_text(render_html(report, run_dir=run_dir))
        (run_dir / "provenance.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False))

        m = {"modules_reported": len(modules), "report": str(run_dir / "report.html")}
        return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, m), m)
