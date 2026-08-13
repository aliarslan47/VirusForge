"""V06 — Genome Annotation (Pharokka; PHANOTATE/Prodigal-gv/tRNAscan-SE içeride)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .. import tools
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_rna, latest_genome, safe_run


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


def parse_vadr(out_dir) -> dict:
    """VADR v-annotate.pl çıktı dizini → {pass, n_pass, n_fail, alerts, n_alerts}.
    pass/fail sınıfı `*.vadr.pass.list`/`*.vadr.fail.list` sekans satırlarından; alert'ler
    `*.vadr.alt.list`ten (# yorum satırları hariç). RNA anotasyon/doğrulama."""
    d = Path(out_dir)

    def _seq_lines(pattern):
        f = next(d.glob(pattern), None)
        if not f or not f.exists():
            return []
        return [l for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")]

    n_pass = len(_seq_lines("*.vadr.pass.list"))
    n_fail = len(_seq_lines("*.vadr.fail.list"))
    alerts = _seq_lines("*.vadr.alt.list")
    return {"pass": (n_fail == 0 and n_pass > 0), "n_pass": n_pass, "n_fail": n_fail,
            "alerts": alerts, "n_alerts": len(alerts)}


def parse_cds_genes(merged_tsv) -> list:
    """pharokka_cds_final_merged_output.tsv → her CDS için gen kaydı (rapor gen-listesi tablosu).
    Sütunlar: gene(locus) / start / stop / strand / annot(=product) / phrog / category."""
    import csv
    genes = []
    with open(merged_tsv, newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            genes.append({
                "gene": (row.get("gene") or "").strip(),
                "start": (row.get("start") or "").strip(),
                "stop": (row.get("stop") or "").strip(),
                "strand": (row.get("strand") or "").strip(),
                "product": (row.get("annot") or "").strip(),
                "phrog": (row.get("phrog") or "").strip(),
                "category": (row.get("category") or "").strip(),
            })
    return genes


class V06Annotate(Module):
    name = "Genome Annotation"
    code = "V06"
    dirname = "V06_GENOME_ANNOTATION"

    def _protein_faa(self, native_dir) -> str:
        """Pharokka protein FASTA'sı: gen-çağırıcıya göre phanotate.faa | prodigal.faa
        (pharokka.faa DEĞİL). terL.faa hariç herhangi bir .faa fallback."""
        d = Path(native_dir)
        for name in ("phanotate.faa", "prodigal.faa", "pharokka.faa"):
            if (d / name).exists():
                return str(d / name)
        for f in sorted(d.glob("*.faa")):
            if f.name != "terL.faa":
                return str(f)
        return str(d / "phanotate.faa")

    def _pharokka_artifacts(self, run_dir) -> dict:
        out = self.module_dir(run_dir) / "03_native_outputs" / "pharokka"
        return {"faa": self._protein_faa(out), "gbk": str(out / "pharokka.gbk"),
                "gff": str(out / "pharokka.gff"), "native_dir": str(out)}

    def restore_artifacts(self, ctx: Context) -> None:
        """Resume: pharokka çıktı yolları V08 (AMR) için ctx'e geri yüklenir."""
        art = self._pharokka_artifacts(ctx.run_dir)
        if Path(art["native_dir"]).exists():
            ctx.artifacts[self.code] = art

    def _run_vadr(self, ctx: Context, dirs, genome) -> ModuleResult:
        """RNA virüs anotasyon/doğrulama (VADR). Pharokka'nın DNA'daki yerini RNA'da alır."""
        out = dirs["03_native_outputs"] / "vadr"          # VADR dizini kendi oluşturur
        err = safe_run(tools.vadr_cmd(genome, out,
                                      get(ctx.cfg, "tools.vadr.db", "databases/vadr"),
                                      get(ctx.cfg, "tools.vadr.model", "sarscov2"),
                                      get(ctx.cfg, "tools.vadr.conda_env", None),
                                      get(ctx.cfg, "tools.vadr.conda_bin", "conda")),
                       dirs["07_logs"] / "vadr.log")
        if err or not out.exists():
            m = {"annotation": "VADR", "error": err or "VADR çıktısı bulunamadı"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)
        metrics = {"annotation": "VADR", "model": get(ctx.cfg, "tools.vadr.model", "sarscov2"),
                   **parse_vadr(out)}
        (dirs["04_standardized"] / "annotation_summary.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        status = Status.PASS if metrics.get("pass") else Status.WARNING
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        genome = latest_genome(ctx)
        if not genome:
            m = {"error": "girdi genom bulunamadı"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        if is_rna(ctx):                                   # RNA → VADR (Pharokka faj-özel, DNA yolunda)
            return self._run_vadr(ctx, dirs, genome)

        db = get(ctx.cfg, "tools.pharokka.db", "databases/pharokka")
        out = dirs["03_native_outputs"] / "pharokka"
        err = safe_run(tools.pharokka_cmd(genome, out, db, get(ctx.cfg, "general.threads", 8)),
                       dirs["07_logs"] / "pharokka.log")
        cds_fn = out / "pharokka_cds_functions.tsv"
        if not err and cds_fn.exists():
            metrics = parse_pharokka(cds_fn)
            metrics["identifier_integrity"] = "locus_tag/gene/product/protein_id ayrı; bilinmeyen product=NULL"
            merged = out / "pharokka_cds_final_merged_output.tsv"
            if merged.exists():
                metrics["genes"] = parse_cds_genes(merged)
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
        # pharokka çıktı yollarını aşağı-akışa yayınla (V08 AMR proteinleri)
        if status == Status.PASS:
            ctx.artifacts[self.code] = self._pharokka_artifacts(ctx.run_dir)
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
