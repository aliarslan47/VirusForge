"""Harici araç komut kurucuları (saf fonksiyonlar — test edilebilir).

Her fonksiyon list[str] döndürür; çalıştırma util.run_cmd/run_redirect ile yapılır.
"""
from __future__ import annotations

from pathlib import Path


def fastp_cmd(r1, r2, out_dir, threads=8, extra=""):
    out = Path(out_dir)
    cmd = ["fastp", "-i", str(r1), "-I", str(r2),
           "-o", str(out / "clean_R1.fastq.gz"), "-O", str(out / "clean_R2.fastq.gz"),
           "-j", str(out / "fastp.json"), "-h", str(out / "fastp.html"),
           "-w", str(threads)]
    if extra:
        cmd += extra.split()
    return cmd


def fastqc_cmd(inputs, out_dir, threads=8):
    return ["fastqc", "-t", str(threads), "-o", str(out_dir), *[str(i) for i in inputs]]


def nanoplot_cmd(long_reads, out_dir, threads=8, conda_env=None, conda_bin="conda"):
    return _conda_wrap(["NanoPlot", "--fastq", str(long_reads), "-o", str(out_dir),
                        "-t", str(threads)], conda_env, conda_bin)


def filtlong_cmd(long_reads, min_length=1000, keep_percent=90, conda_env=None, conda_bin="conda"):
    return _conda_wrap(["filtlong", "--min_length", str(min_length),
                        "--keep_percent", str(keep_percent), str(long_reads)], conda_env, conda_bin)


def multiqc_cmd(scan_dir, out_dir):
    return ["multiqc", str(scan_dir), "-o", str(out_dir), "-f"]


def spades_cmd(r1, r2, out_dir, threads=8, careful=True):
    cmd = ["spades.py", "-1", str(r1), "-2", str(r2), "-o", str(out_dir), "-t", str(threads)]
    if careful:
        cmd.append("--careful")
    return cmd


def flye_cmd(long_reads, out_dir, chemistry="r10", threads=8, conda_env=None, conda_bin="conda"):
    # R10 → --nano-hq, R9 → --nano-raw (kimya-otomatik; BacForge dersi)
    # --meta: küçük + ultra-yüksek kapsamlı viral genomlar için şart (T7 doğrulamasında bulundu;
    # --meta olmadan Flye "No disjointigs assembled" ile çöküyor)
    flag = "--nano-hq" if str(chemistry).lower().startswith("r10") else "--nano-raw"
    return _conda_wrap(["flye", flag, str(long_reads), "--meta", "-o", str(out_dir), "-t", str(threads)],
                       conda_env, conda_bin)


def unicycler_cmd(r1, r2, long_reads, out_dir, threads=8, conda_env=None, conda_bin="conda"):
    return _conda_wrap(["unicycler", "-1", str(r1), "-2", str(r2), "-l", str(long_reads),
                        "-o", str(out_dir), "-t", str(threads)], conda_env, conda_bin)


def medaka_consensus_cmd(long_reads, draft, out_dir, model="r1041_e82_400bps_sup_v5.0.0",
                         threads=8, conda_env=None, conda_bin="conda"):
    return _conda_wrap(["medaka_consensus", "-i", str(long_reads), "-d", str(draft),
                        "-o", str(out_dir), "-m", model, "-t", str(threads)], conda_env, conda_bin)


def quast_cmd(genome, out_dir, threads=8):
    return ["quast.py", str(genome), "-o", str(out_dir), "-t", str(threads)]


def checkv_cmd(genome, out_dir, db, threads=8):
    return ["checkv", "end_to_end", str(genome), str(out_dir), "-d", str(db), "-t", str(threads)]


def genomad_cmd(genome, out_dir, db, threads=8):
    return ["genomad", "end-to-end", "--cleanup", str(genome), str(out_dir), str(db), "-t", str(threads)]


def mash_sketch_indiv_cmd(fasta, out_prefix):
    """mash sketch -i: multifasta'daki HER kaydı ayrı sketch'le (all-vs-all mesafe için)."""
    return ["mash", "sketch", "-i", "-o", str(out_prefix), str(fasta)]


def mash_dist_table_cmd(msh):
    """mash dist -t: sketch'i kendisiyle karşılaştır → kare mesafe tablosu (all-vs-all)."""
    return ["mash", "dist", "-t", str(msh), str(msh)]


def mash_dist_cmd(ref_sketch, query):
    return ["mash", "dist", str(ref_sketch), str(query)]


def pharokka_cmd(genome, out_dir, db, threads=8):
    return ["pharokka.py", "-i", str(genome), "-o", str(out_dir), "-d", str(db),
            "-t", str(threads), "-f"]


def pharokka_plotter_cmd(genome, pharokka_out, name="genome_map", title="phage"):
    # pharokka çıktısındaki gff/gbk'den circular genom haritası (PNG) üretir
    return ["pharokka_plotter.py", "-i", str(genome), "-o", str(pharokka_out),
            "-n", name, "-t", str(title)]


# ---- M2-A faj zenginleştirme araçları ----

def rnaviralspades_cmd(r1, r2, out_dir, threads=8):
    """rnaviralSPAdes: RNA-virüs de novo assembly (spades.py --rnaviral). Base env (spades)."""
    return ["spades.py", "--rnaviral", "-1", str(r1), "-2", str(r2),
            "-o", str(out_dir), "-t", str(threads)]


def minimap2_cmd(reference, reads, threads=8, preset="sr", conda_env=None, conda_bin="conda"):
    """minimap2 hizalama → SAM (stdout, run_redirect ile). reads = tek dosya veya [r1,r2] listesi.
    preset 'sr'=kısa okuma, 'map-ont'=ONT."""
    rlist = [str(r) for r in (reads if isinstance(reads, (list, tuple)) else [reads])]
    cmd = ["minimap2", "-ax", preset, "-t", str(threads), str(reference), *rlist]
    return _conda_wrap(cmd, conda_env, conda_bin)


def samtools_sort_cmd(in_path, out_bam, threads=8, conda_env=None, conda_bin="conda"):
    return _conda_wrap(["samtools", "sort", "-@", str(threads), "-o", str(out_bam), str(in_path)],
                       conda_env, conda_bin)


def samtools_index_cmd(bam, conda_env=None, conda_bin="conda"):
    return _conda_wrap(["samtools", "index", str(bam)], conda_env, conda_bin)


def samtools_depth_cmd(bam, conda_env=None, conda_bin="conda"):
    """samtools depth -a: HER pozisyonda derinlik (stdout, run_redirect). Breadth/mean için
    (sürümden bağımsız; samtools 1.9'da 'coverage' yok, 'depth' var)."""
    return _conda_wrap(["samtools", "depth", "-a", str(bam)], conda_env, conda_bin)


def samtools_mpileup_cmd(reference, bam, conda_env=None, conda_bin="conda"):
    """ivar consensus için mpileup (önerilen bayraklar: -aa -A -d 0 -Q 0). Pipe'ın 1. komutu."""
    cmd = ["samtools", "mpileup", "-aa", "-A", "-d", "0", "-Q", "0",
           "--reference", str(reference), str(bam)]
    return _conda_wrap(cmd, conda_env, conda_bin, stream=True)


def ivar_consensus_cmd(out_prefix, min_depth=10, min_freq=0.5, conda_env=None, conda_bin="conda"):
    """ivar consensus: mpileup'ı STDIN'den okur (pipe 2. komutu). -m min derinlik, -t min frekans."""
    cmd = ["ivar", "consensus", "-p", str(out_prefix), "-m", str(min_depth), "-t", str(min_freq)]
    return _conda_wrap(cmd, conda_env, conda_bin, stream=True)


def ivar_trim_cmd(bam, primer_bed, out_prefix, conda_env=None, conda_bin="conda"):
    """ivar trim: ARTIC amplikon primer kırpma (BAM in → BAM out_prefix)."""
    cmd = ["ivar", "trim", "-i", str(bam), "-b", str(primer_bed), "-p", str(out_prefix)]
    return _conda_wrap(cmd, conda_env, conda_bin)


def vadr_cmd(genome, out_dir, model_dir, model_key, conda_env=None, conda_bin="conda"):
    """VADR v-annotate.pl: RNA virüs anotasyon/doğrulama (pass/fail + alert). İzole vf_vadr env."""
    cmd = ["v-annotate.pl", "--mdir", str(model_dir), "--mkey", str(model_key),
           str(genome), str(out_dir)]
    return _conda_wrap(cmd, conda_env, conda_bin)


def _conda_wrap(cmd, conda_env=None, conda_bin="conda", stream=False):
    """Araç izole bir conda env'inde ise `conda run -n <env>` ile sar (phabox deseni;
    çalışan virusforge env'ini korur). stream=True → `--no-capture-output` (pipe'ta stdout
    tamponlanmasın; `samtools mpileup | ivar consensus` gibi)."""
    if conda_env:
        pre = [conda_bin, "run", "-n", conda_env]
        if stream:
            pre.append("--no-capture-output")
        return [*pre, *cmd]
    return cmd


def amrfinder_cmd(input_path, out_tsv, db="", is_protein=True, threads=8,
                  conda_env=None, conda_bin="conda"):
    """AMRFinderPlus: proteinlerde (-p) veya genomda (-n) AMR/virülans/stres taraması."""
    flag = "-p" if is_protein else "-n"
    cmd = ["amrfinder", flag, str(input_path), "-o", str(out_tsv), "--threads", str(threads)]
    if db:
        cmd += ["-d", str(db)]
    return _conda_wrap(cmd, conda_env, conda_bin)


def phabox_cmd(genome, out_dir, db, threads=8, conda_env=None, conda_bin="conda"):
    base = ["phabox2", "--task", "end_to_end", "--contigs", str(genome),
            "--outpth", str(out_dir), "--dbdir", str(db), "--threads", str(threads)]
    # phabox pandas-2 uyumsuz → kendi izole env'inde çalıştır (conda run)
    if conda_env:
        return [conda_bin, "run", "-n", conda_env, *base]
    return base


# ---- M3 karşılaştırmalı & filogeni araçları ----

def blastn_remote_cmd(query, out_tsv, db="ref_viruses_rep_genomes", max_target_seqs=50):
    """Online blastn (DB indirmesi YOK): örneği NCBI viral DB'ye karşı çalıştır, tabular çıktı."""
    return ["blastn", "-query", str(query), "-db", str(db), "-remote",
            "-max_target_seqs", str(max_target_seqs),
            "-outfmt", "6 sacc staxids sscinames pident qcovs length evalue bitscore",
            "-out", str(out_tsv)]


def efetch_cmd(accession, out_fasta):
    """Entrez Direct efetch: accession'ın tam genom FASTA'sı (util.run_redirect ile stdout→dosya)."""
    return ["efetch", "-db", "nucleotide", "-id", str(accession), "-format", "fasta"]


def mafft_cmd(in_fasta, out_aln):
    """MAFFT tüm-genom hizalama (stdout→out_aln). --adjustdirection: ters-tümleyen
    genomları otomatik çevir (aksi halde farklı yönelim → sahte uzun dal)."""
    return ["mafft", "--auto", "--adjustdirection", str(in_fasta)]


def iqtree_cmd(aln, prefix, threads=8, binary="iqtree"):
    """IQ-TREE (v2/v3) ML ağaç + UFBoot bootstrap, model-otomatik. Binary adı sistemde
    değişebilir (v3 = 'iqtree'); config'le override edilebilir."""
    return [binary, "-s", str(aln), "--prefix", str(prefix),
            "-B", "1000", "-T", str(threads), "-m", "MFP", "--quiet"]


def taxmyphage_cmd(genome, out_dir, threads=8):
    """taxmyPHAGE: VIRIDIC + ICTV VMR → cins/tür."""
    return ["taxmyphage", "run", "-i", str(genome), "-o", str(out_dir), "-t", str(threads)]


def makeblastdb_prot_cmd(faa, db_prefix):
    """Yerel protein BLAST DB (synteny homolog eşleme için)."""
    return ["makeblastdb", "-in", str(faa), "-dbtype", "prot", "-out", str(db_prefix)]


def clinker_cmd(gbks, out_html, conda_env=None, conda_bin="conda", extra=None):
    """clinker: çok-genomlu interaktif gen-kümesi hizalaması → taşınabilir HTML (-p).
    Girdi = anotasyonlu GenBank listesi; izole `ali-clinker` env'inde koşar (conda_env)."""
    cmd = ["clinker", *[str(g) for g in gbks]]
    if extra:
        cmd += list(extra)
    cmd += ["-p", str(out_html)]
    return _conda_wrap(cmd, conda_env, conda_bin)


def makeblastdb_nucl_cmd(fasta, db_prefix):
    """Yerel nükleotid BLAST DB (çoklu-örnek all-vs-all için)."""
    return ["makeblastdb", "-in", str(fasta), "-dbtype", "nucl", "-out", str(db_prefix)]


def blastn_local_cmd(query_fasta, db_prefix, out_tsv, threads=8):
    """Yerel all-vs-all blastn (örnekler-arası % kimlik); qseqid sseqid pident length."""
    return ["blastn", "-query", str(query_fasta), "-db", str(db_prefix),
            "-num_threads", str(threads), "-max_target_seqs", "1000",
            "-outfmt", "6 qseqid sseqid pident length", "-out", str(out_tsv)]


def blastp_cmd(query_faa, db_prefix, out_tsv, threads=8):
    """Yerel blastp: örnek proteinleri ref proteinlerine karşı (homolog gen çiftleri)."""
    return ["blastp", "-query", str(query_faa), "-db", str(db_prefix),
            "-max_target_seqs", "1", "-evalue", "1e-5", "-num_threads", str(threads),
            "-outfmt", "6 qseqid sseqid pident bitscore", "-out", str(out_tsv)]
