"""V02 — Viral Genome Assembly (SPAdes/Flye/Unicycler yönlendirme)."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_rna, safe_run


# Flye --nano-hq (R10) yalnız düşük-hatalı okumalar için; yüksek-hatalı (R9-tipi)
# veride çöker ("No disjointigs assembled"). Ortalama okuma kalitesiyle otomatik seç.
_HQ_QUAL_THRESHOLD = 13.0   # ~ Q13 (<%5 hata) altı → R9 (--nano-raw)


def _read_fasta(path) -> dict:
    recs, name, seq = {}, None, []
    for line in Path(path).read_text().splitlines():
        if line.startswith(">"):
            if name:
                recs[name] = "".join(seq)
            name, seq = line[1:].split()[0], []
        else:
            seq.append(line.strip())
    if name:
        recs[name] = "".join(seq)
    return recs


def sanitize_contig_names(fasta_in, fasta_out) -> None:
    """Salt-sayısal contig header'larını 'contig_<n>' yap. Unicycler '>1' adları PhaBOX'ı
    çökertiyor (pandas int64/object merge). Sayısal-olmayan adlar (NODE_1, contig_3) korunur."""
    recs = _read_fasta(fasta_in)
    with open(fasta_out, "w") as fh:
        for name, seq in recs.items():
            safe = f"contig_{name}" if name.isdigit() else name
            fh.write(f">{safe}\n{seq}\n")


def filter_contigs_by_coverage(assembly_info_path, fasta_in, fasta_out, min_frac=0.1):
    """Flye assembly_info.txt'ten kapsamları oku; max_cov*min_frac altındaki junk contig'leri at.
    Kalan contig'leri fasta_out'a yaz, tutulan isimleri döndür (uzunluğa göre sıralı).
    Gerçek T7 long doğrulamasında: ana faj 1911x, host/kimera junk 3-22x → downstream kirlenmesi."""
    covs, lens = {}, {}
    for line in Path(assembly_info_path).read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = line.split("\t")
        try:
            covs[p[0]] = float(p[2])
            lens[p[0]] = int(p[1])
        except (IndexError, ValueError):
            continue
    if not covs:
        return None
    thr = max(covs.values()) * min_frac
    keep = {n for n, c in covs.items() if c >= thr}
    recs = _read_fasta(fasta_in)
    with open(fasta_out, "w") as fh:
        for n in recs:
            if n in keep:
                fh.write(f">{n}\n{recs[n]}\n")
    return sorted(keep, key=lambda n: -lens.get(n, 0))


def resolve_chemistry(mean_qual) -> str:
    """NanoPlot ortalama kalitesinden ONT kimyası: düşük kalite→r9, yüksek→r10.
    Bilinmiyorsa modern varsayılan r10 (gerçek T7 doğrulamasında bulundu)."""
    if mean_qual is None:
        return "r10"
    return "r10" if float(mean_qual) >= _HQ_QUAL_THRESHOLD else "r9"


def select_assembler(mode: str, reads: dict, out_dir, cfg: dict, mean_qual=None):
    """(cmd, üretilecek contig dosyası) döndür. Gerekli okuma yoksa ValueError (sessiz PASS yasak)."""
    threads = get(cfg, "general.threads", 8)
    lenv = get(cfg, "tools.long.conda_env", None)
    lbin = get(cfg, "tools.long.conda_bin", "conda")
    out = Path(out_dir)
    # RNA + kısa okuma + referans YOK → de novo rnaviralSPAdes (referans varsa run() konsensus yolunu seçer)
    molecule = str(get(cfg, "general.molecule", "auto")).lower()
    if molecule == "rna" and mode == "SHORT_READ":
        if not (reads.get("r1") and reads.get("r2")):
            raise ValueError("RNA SHORT_READ için R1/R2 bulunamadı")
        return tools.rnaviralspades_cmd(reads["r1"], reads["r2"], out, threads), out / "contigs.fasta"
    if mode == "SHORT_READ":
        if not (reads.get("r1") and reads.get("r2")):
            raise ValueError("SHORT_READ için R1/R2 bulunamadı")
        return tools.spades_cmd(reads["r1"], reads["r2"], out, threads,
                                get(cfg, "tools.spades.careful", True)), out / "contigs.fasta"
    if mode == "LONG_READ":
        if not reads.get("long"):
            raise ValueError("LONG_READ için uzun-okuma bulunamadı")
        chem = get(cfg, "tools.flye.chemistry", "auto")
        if str(chem).lower() == "auto":
            chem = resolve_chemistry(mean_qual)   # kaliteye-dayalı R9/R10 (Q<13 → --nano-raw)
        return tools.flye_cmd(reads["long"], out, chem, threads,
                              conda_env=lenv, conda_bin=lbin), out / "assembly.fasta"
    if mode == "HYBRID":
        if not (reads.get("r1") and reads.get("r2") and reads.get("long")):
            raise ValueError("HYBRID için short+long birlikte gerekli")
        return tools.unicycler_cmd(reads["r1"], reads["r2"], reads["long"], out, threads,
                                   conda_env=lenv, conda_bin=lbin), out / "assembly.fasta"
    raise ValueError(f"assembly bu modda çalışmaz: {mode}")


def clean_consensus_gaps(src, dst) -> None:
    """iVar konsensus'unda düşük-derinlik/no-call pozisyonları '-' olabilir; VADR (esl-reformat)
    yalnız ACGTN/IUPAC kabul eder → dizi satırlarındaki '-' karakterlerini 'N'e çevir."""
    out = []
    for line in Path(src).read_text().splitlines():
        out.append(line if line.startswith(">") else line.replace("-", "N"))
    Path(dst).write_text("\n".join(out) + "\n")


class V02Assembly(Module):
    name = "Viral Genome Assembly"
    code = "V02"
    dirname = "V02_VIRAL_ASSEMBLY"

    def restore_artifacts(self, ctx: Context) -> None:
        base = self.module_dir(ctx.run_dir) / "04_standardized"
        draft = base / "draft_viral_genome.fasta"
        if draft.exists():
            art = {"draft": str(draft)}
            bam = base / "aligned_sorted.bam"          # RNA referans-tabanlı → Faz 2 varyant için
            if bam.exists():
                art["bam"] = str(bam)
            ctx.artifacts[self.code] = art

    def _run_reference_consensus(self, ctx: Context, dirs, reads, ref) -> ModuleResult:
        """RNA referans-tabanlı konsensus: minimap2 → samtools sort → (primer varsa ivar trim) →
        mpileup | ivar consensus → draft + BAM artifact (BAM Faz 2 varyant çağırma için saklanır)."""
        env = get(ctx.cfg, "tools.rna.conda_env", None)
        cbin = get(ctx.cfg, "tools.rna.conda_bin", "conda")
        threads = get(ctx.cfg, "general.threads", 8)
        work = dirs["02_work"]
        logs = dirs["07_logs"]
        rlist = [r for r in (reads.get("r1"), reads.get("r2")) if r] or [reads.get("long")]
        if not any(rlist):
            m = {"error": "RNA konsensus için okuma bulunamadı"}
            return ModuleResult(Status.FAIL, self.write_summary(ctx.run_dir, Status.FAIL, m), m)
        preset = "map-ont" if (ctx.mode == "LONG_READ") else "sr"

        sam = work / "aln.sam"
        err = None
        try:
            util.run_redirect(tools.minimap2_cmd(ref, rlist, threads, preset, env, cbin), sam,
                              logs / "minimap2.log")
        except RuntimeError as exc:
            err = str(exc)
        sorted_bam = dirs["04_standardized"] / "aligned_sorted.bam"
        if not err:
            primer_bed = get(ctx.cfg, "tools.rna.primer_bed", "")
            if primer_bed:
                pre_bam = work / "aligned.bam"
                err = (safe_run(tools.samtools_sort_cmd(sam, pre_bam, threads, env, cbin), logs / "sort1.log")
                       or safe_run(tools.samtools_index_cmd(pre_bam, env, cbin), logs / "index1.log"))
                if not err:
                    trimmed = work / "trimmed"        # ivar trim → trimmed.bam
                    err = safe_run(tools.ivar_trim_cmd(pre_bam, primer_bed, trimmed, env, cbin),
                                   logs / "ivar_trim.log")
                    src = str(trimmed) + ".bam"
                    err = err or safe_run(tools.samtools_sort_cmd(src, sorted_bam, threads, env, cbin),
                                          logs / "sort2.log")
            else:
                err = safe_run(tools.samtools_sort_cmd(sam, sorted_bam, threads, env, cbin), logs / "sort.log")
            err = err or safe_run(tools.samtools_index_cmd(sorted_bam, env, cbin), logs / "index.log")

        prefix = work / "consensus"
        if not err:
            try:
                util.run_pipe(tools.samtools_mpileup_cmd(ref, sorted_bam, env, cbin),
                              tools.ivar_consensus_cmd(prefix,
                                                       get(ctx.cfg, "tools.rna.ivar_min_depth", 10),
                                                       get(ctx.cfg, "tools.rna.ivar_min_freq", 0.5), env, cbin),
                              work / "ivar_consensus.stdout", logs / "consensus.log")
            except RuntimeError as exc:
                err = str(exc)
        cons_fa = Path(str(prefix) + ".fa")
        if err or not cons_fa.exists() or cons_fa.stat().st_size == 0:
            m = {"error": err or "konsensus üretilmedi", "reference": str(ref)}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        draft = dirs["04_standardized"] / "draft_viral_genome.fasta"
        clean_consensus_gaps(cons_fa, draft)          # iVar '-' (no-call) → N (VADR uyumu)
        m = {"assembler": "referans-tabanlı (iVar consensus)", "reference": str(ref),
             "bam": str(sorted_bam), "consensus": str(draft), "draft": str(draft)}
        ctx.artifacts[self.code] = {"draft": str(draft), "bam": str(sorted_bam), "reference": str(ref)}
        ctx.results[self.code] = m
        return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, m), m)

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if ctx.mode == "ASSEMBLY_INPUT":
            # hazır assembly'yi doğrudan draft yap
            fa = next((p for p in Path(ctx.sample_dir).iterdir()
                       if p.name.lower().endswith((".fasta", ".fa", ".fna"))), None)
            if fa:
                draft = dirs["04_standardized"] / "draft_viral_genome.fasta"
                sanitize_contig_names(fa, draft)   # sayısal header temizle (PhaBOX güvenliği)
                ctx.artifacts[self.code] = {"draft": str(draft)}
                m = {"source": "assembly_input", "assembler": "(hazır assembly)", "draft": str(draft)}
                return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, m), m)

        v01 = ctx.artifacts.get("V01", {})
        raw_short = util.find_short_reads(ctx.sample_dir)
        raw_long = util.find_long_reads(ctx.sample_dir)
        reads = {
            "r1": v01.get("clean_r1") or (str(raw_short[0]) if raw_short else None),
            "r2": v01.get("clean_r2") or (str(raw_short[1]) if raw_short else None),
            "long": v01.get("clean_long") or (str(raw_long) if raw_long else None),
        }
        # RNA + referans verildiyse → referans-tabanlı iVar konsensus (de novo yerine)
        if is_rna(ctx) and get(ctx.cfg, "tools.rna.reference", ""):
            return self._run_reference_consensus(ctx, dirs, reads, get(ctx.cfg, "tools.rna.reference"))

        work = dirs["02_work"] / "asm"
        mean_qual = (ctx.results.get("V01", {}).get("long") or {}).get("mean_qual")
        try:
            cmd, contig = select_assembler(ctx.mode, reads, work, ctx.cfg, mean_qual=mean_qual)
        except ValueError as exc:
            m = {"error": str(exc)}
            return ModuleResult(Status.FAIL, self.write_summary(ctx.run_dir, Status.FAIL, m), m)

        err = safe_run(cmd, dirs["07_logs"] / "assembly.log")
        if err or not Path(contig).exists():
            m = {"assembler_cmd": cmd[0], "error": err or f"contig üretilmedi: {contig}"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        draft = dirs["04_standardized"] / "draft_viral_genome.fasta"
        # gerçek assembler adı (conda-sarmalı komutta cmd[0]=conda olur)
        _names = {"SHORT_READ": "SPAdes", "LONG_READ": "Flye", "HYBRID": "Unicycler"}
        asm_name = "rnaviralSPAdes" if "--rnaviral" in cmd else _names.get(ctx.mode, cmd[0])
        m = {"assembler": asm_name}
        # Flye (long) çıktısında düşük-kapsamlı junk contig'leri ele (host/kimera → downstream kirlenmesi)
        info = Path(work) / "assembly_info.txt"
        kept = None
        if info.exists():
            min_frac = get(ctx.cfg, "tools.flye.min_cov_fraction", 0.1)
            kept = filter_contigs_by_coverage(info, contig, draft, min_frac)
        if not kept or not draft.exists() or draft.stat().st_size == 0:
            sanitize_contig_names(contig, draft)   # filtre yoksa: sayısal header'ları temizle (Unicycler '>1')
        else:
            m["kept_contigs"] = kept
            m["dropped_low_coverage"] = True
        m["draft"] = str(draft)
        ctx.artifacts[self.code] = {"draft": str(draft)}
        ctx.results[self.code] = m
        return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, m), m)
