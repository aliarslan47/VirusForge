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

def _conda_wrap(cmd, conda_env=None, conda_bin="conda"):
    """Araç izole bir conda env'inde ise `conda run -n <env>` ile sar (phabox deseni;
    çalışan virusforge env'ini korur)."""
    if conda_env:
        return [conda_bin, "run", "-n", conda_env, *cmd]
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


def blastp_cmd(query_faa, db_prefix, out_tsv, threads=8):
    """Yerel blastp: örnek proteinleri ref proteinlerine karşı (homolog gen çiftleri)."""
    return ["blastp", "-query", str(query_faa), "-db", str(db_prefix),
            "-max_target_seqs", "1", "-evalue", "1e-5", "-num_threads", str(threads),
            "-outfmt", "6 qseqid sseqid pident bitscore", "-out", str(out_tsv)]
