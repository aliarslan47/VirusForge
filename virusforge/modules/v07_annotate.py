"""V07 — Genome Annotation (Pharokka; PHANOTATE/Prodigal-gv/tRNAscan-SE içeride)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, latest_genome, safe_run


def parse_pharokka(cds_functions_tsv) -> dict:
    """pharokka_cds_functions.tsv: Description<TAB>Count<TAB>contig — CONTIG BAŞINA satır.
    Kategorileri tüm contig'ler üzerinden TOPLA (son satırı almak yanlış: BacForge dersi)."""
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
    return {
        "cds": counts.get("CDS"),
        "trna": counts.get("tRNAs") or counts.get("tRNA"),
        "functions": counts,
    }


class V07Annotate(Module):
    name = "Genome Annotation"
    code = "V07"
    dirname = "V07_GENOME_ANNOTATION"

    def _pharokka_artifacts(self, run_dir) -> dict:
        out = self.module_dir(run_dir) / "03_native_outputs" / "pharokka"
        return {"faa": str(out / "pharokka.faa"), "gbk": str(out / "pharokka.gbk"),
                "gff": str(out / "pharokka.gff"), "native_dir": str(out)}

    def restore_artifacts(self, ctx: Context) -> None:
        """Resume: pharokka çıktı yolları V11/V13 için ctx'e geri yüklenir."""
        art = self._pharokka_artifacts(ctx.run_dir)
        if Path(art["native_dir"]).exists():
            ctx.artifacts[self.code] = art

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        genome = latest_genome(ctx)
        if not genome:
            m = {"error": "girdi genom bulunamadı"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        db = get(ctx.cfg, "tools.pharokka.db", "databases/pharokka")
        out = dirs["03_native_outputs"] / "pharokka"
        err = safe_run(tools.pharokka_cmd(genome, out, db, get(ctx.cfg, "general.threads", 8)),
                       dirs["07_logs"] / "pharokka.log")
        cds_fn = out / "pharokka_cds_functions.tsv"
        if not err and cds_fn.exists():
            metrics = parse_pharokka(cds_fn)
            metrics["identifier_integrity"] = "locus_tag/gene/product/protein_id ayrı; bilinmeyen product=NULL"
            status = Status.PASS
            # circular genom haritası (otomatik — kullanıcı istemeden)
            title = Path(ctx.sample_dir).name
            safe_run(tools.pharokka_plotter_cmd(genome, out, "genome_map", title),
                     dirs["07_logs"] / "pharokka_plot.log")
            png = out / "genome_map.png"
            if png.exists():
                shutil.copy(png, dirs["06_visualization"] / "genome_map.png")
                metrics["genome_map"] = "06_visualization/genome_map.png"
        else:
            metrics = {"error": err or "Pharokka çıktısı bulunamadı"}
            status = Status.WARNING
        (dirs["04_standardized"] / "annotation_summary.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        # pharokka çıktı yollarını aşağı-akışa yayınla (V11 AMR proteinler, V13 phold GenBank)
        if status == Status.PASS:
            ctx.artifacts[self.code] = self._pharokka_artifacts(ctx.run_dir)
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
