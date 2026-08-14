"""V11 — Variant & Quasispecies Calling (RNA yolu, Faz 2).

RNA virüslerinde konsensus-seviyesi + düşük-frekanslı (intra-host / quasispecies) varyantlar.
iVar variants (frekanslı tablo, amplikon-uyumlu) + LoFreq (duyarlı düşük-frekans). Faz 1'in ürettiği
referans-hizalı BAM (`ctx.artifacts["V02"]["bam"]`) üzerinden. DNA/faj yolunda veya BAM yoksa N/A.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_rna, safe_run


def parse_gene_intervals(gff_path) -> list:
    """GFF → [(gen_adı, start, end)]. Ad: gene_name= / Name= / gene= / ID= / product=.
    Varyantı hangi CDS/gene düştüğünü pozisyonla eşlemek için (çeviri gerektirmez)."""
    out = []
    try:
        with open(gff_path) as fh:
            for line in fh:
                if line.startswith("#") or not line.strip():
                    continue
                cols = line.rstrip("\n").split("\t")
                if len(cols) < 9 or cols[2].lower() not in ("gene", "cds", "mature_protein_region_of_cds"):
                    continue
                try:
                    start, end = int(cols[3]), int(cols[4])
                except ValueError:
                    continue
                name = ""
                for key in ("gene_name=", "Name=", "gene=", "product=", "ID="):
                    if key in cols[8]:
                        name = cols[8].split(key)[1].split(";")[0].strip()
                        break
                if name:
                    out.append((name, min(start, end), max(start, end)))
    except (OSError, TypeError):
        pass
    return out


def gene_at(pos, intervals) -> str:
    """pos hangi gen(ler)e düşüyor? Örtüşen gen adları ('/' ile birleşik); yoksa ''."""
    try:
        pos = int(pos)
    except (TypeError, ValueError):
        return ""
    hits = [name for (name, s, e) in intervals if s <= pos <= e]
    return "/".join(dict.fromkeys(hits)) if hits else ""


def fasta_first_id(path) -> str:
    """Referans FASTA'nın ilk header id'si (accession) — varyant koordinat sistemi.
    Dosya yok/başlıksız → yolun dosya-kök adı (yine de dürüst bir tanımlayıcı)."""
    try:
        with open(path) as fh:
            for line in fh:
                if line.startswith(">"):
                    return line[1:].split()[0].strip()
    except (OSError, TypeError):
        pass
    return Path(str(path)).stem if path else ""


def parse_ivar_variants(tsv_path) -> list:
    """iVar variants TSV → [{pos,ref,alt,freq,depth,aa}]. aa = REF_AA→ALT_AA (varsa)."""
    import csv
    out = []
    with open(tsv_path, newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            try:
                pos = int(r.get("POS"))
            except (TypeError, ValueError):
                continue
            ref_aa, alt_aa = (r.get("REF_AA") or "").strip(), (r.get("ALT_AA") or "").strip()
            aa = f"{ref_aa}→{alt_aa}" if ref_aa and alt_aa else ""
            try:
                freq = float(r.get("ALT_FREQ"))
            except (TypeError, ValueError):
                freq = 0.0
            try:
                depth = int(r.get("TOTAL_DP"))
            except (TypeError, ValueError):
                depth = 0
            out.append({"pos": pos, "ref": (r.get("REF") or "").strip(),
                        "alt": (r.get("ALT") or "").strip(), "freq": freq, "depth": depth, "aa": aa})
    return out


def parse_lofreq_vcf(vcf_path) -> list:
    """LoFreq VCF → [{pos,ref,alt,af,dp}] (INFO'dan AF ve DP)."""
    out = []
    for line in Path(vcf_path).read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 8:
            continue
        info = dict(kv.split("=", 1) for kv in cols[7].split(";") if "=" in kv)
        try:
            af = float(info.get("AF", 0))
        except ValueError:
            af = 0.0
        try:
            dp = int(info.get("DP", 0))
        except ValueError:
            dp = 0
        out.append({"pos": int(cols[1]), "ref": cols[3], "alt": cols[4], "af": af, "dp": dp})
    return out


def variant_summary(variants, key="freq") -> dict:
    """Frekanslara göre özet: konsensus (≥0.5) vs minör/intra-host (<0.5 = quasispecies sinyali)."""
    freqs = [v.get(key, 0.0) for v in variants]
    n_consensus = sum(1 for f in freqs if f >= 0.5)
    n_minor = sum(1 for f in freqs if 0 < f < 0.5)
    return {"n_total": len(variants), "n_consensus": n_consensus, "n_minor": n_minor,
            "quasispecies": n_minor > 0}


class V11VariantCall(Module):
    name = "Variant & Quasispecies Calling"
    code = "V11"
    dirname = "V11_VARIANT_CALLING"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not is_rna(ctx):                               # varyant çağırma yalnız RNA yolunda
            m = {"note": "DNA/faj yolu — varyant/quasispecies çağırma uygulanmadı"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)
        v02 = ctx.artifacts.get("V02", {}) or {}
        bam = v02.get("bam")
        ref = v02.get("reference") or get(ctx.cfg, "tools.rna.reference", "")  # resume dayanıklılığı
        if not bam or not Path(bam).exists() or not ref:
            m = {"note": "referans-tabanlı BAM yok (de novo RNA) — varyant çağrılamaz"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        renv = get(ctx.cfg, "tools.rna.conda_env", None)
        rbin = get(ctx.cfg, "tools.rna.conda_bin", "conda")
        metrics: dict = {}
        problems: list[str] = []
        # Varyant koordinat sistemi = kullanılan referans; accession olmadan pos/ref→alt belirsizdir
        metrics["reference"] = fasta_first_id(ref)

        # iVar variants (mpileup | ivar variants — konsensustaki pipe deseni)
        prefix = dirs["03_native_outputs"] / "ivar_variants"
        gff = get(ctx.cfg, "tools.rna.gff", "") or None
        try:
            util.run_pipe(
                tools.samtools_mpileup_cmd(ref, bam, renv, rbin),
                tools.ivar_variants_cmd(prefix, get(ctx.cfg, "tools.rna.ivar_var_min_q", 20),
                                        get(ctx.cfg, "tools.rna.ivar_var_min_freq", 0.03),
                                        gff, ref if gff else None, renv, rbin),
                dirs["02_work"] / "ivar_variants.stdout", dirs["07_logs"] / "ivar_variants.log")
        except RuntimeError as exc:
            problems.append(f"iVar variants: {str(exc)[:120]}")
        ivar_tsv = Path(str(prefix) + ".tsv")
        if ivar_tsv.exists():
            iv = parse_ivar_variants(ivar_tsv)
            metrics["ivar_variants"] = iv
            metrics.update(variant_summary(iv, "freq"))

        # LoFreq (izole vf_lofreq env) — duyarlı düşük-frekans
        vcf = dirs["03_native_outputs"] / "lofreq.vcf"
        err = safe_run(tools.lofreq_call_cmd(ref, bam, vcf,
                                             get(ctx.cfg, "tools.lofreq.min_cov", 10),
                                             get(ctx.cfg, "tools.lofreq.conda_env", None),
                                             get(ctx.cfg, "tools.lofreq.conda_bin", "conda")),
                       dirs["07_logs"] / "lofreq.log")
        if not err and vcf.exists():
            metrics["lofreq_variants"] = parse_lofreq_vcf(vcf)
        elif err:
            problems.append(f"LoFreq: {err[:120]}")

        # Gen/CDS anotasyonu: her varyant hangi gene düşüyor (pozisyon→gen; çeviri gerektirmez).
        # Gen GFF'i config'ten; yoksa nextclade dataset'inin genome_annotation.gff3'ünden (aynı virüs).
        gene_gff = get(ctx.cfg, "tools.rna.gene_gff", "") or ""
        if not gene_gff:
            ds = get(ctx.cfg, "tools.nextclade.dataset_dir", "")
            if ds:
                cand = Path(ds) / "genome_annotation.gff3"
                if cand.exists():
                    gene_gff = str(cand)
        intervals = parse_gene_intervals(gene_gff) if gene_gff else []
        if intervals:
            for key in ("ivar_variants", "lofreq_variants"):
                for v in metrics.get(key, []) or []:
                    v["gene"] = gene_at(v.get("pos"), intervals)
            metrics["gene_annotated"] = True

        if "ivar_variants" not in metrics and "lofreq_variants" not in metrics:
            metrics["error"] = "; ".join(problems) or "varyant üretilmedi"
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, metrics), metrics)
        if problems:
            metrics["problems"] = problems
        (dirs["04_standardized"] / "variants.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        status = Status.PASS if not problems else Status.WARNING
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
