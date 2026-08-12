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


def nanoplot_cmd(long_reads, out_dir, threads=8):
    return ["NanoPlot", "--fastq", str(long_reads), "-o", str(out_dir), "-t", str(threads)]


def filtlong_cmd(long_reads, min_length=1000, keep_percent=90):
    return ["filtlong", "--min_length", str(min_length),
            "--keep_percent", str(keep_percent), str(long_reads)]


def multiqc_cmd(scan_dir, out_dir):
    return ["multiqc", str(scan_dir), "-o", str(out_dir), "-f"]


def spades_cmd(r1, r2, out_dir, threads=8, careful=True):
    cmd = ["spades.py", "-1", str(r1), "-2", str(r2), "-o", str(out_dir), "-t", str(threads)]
    if careful:
        cmd.append("--careful")
    return cmd


def flye_cmd(long_reads, out_dir, chemistry="r10", threads=8):
    # R10 → --nano-hq, R9 → --nano-raw (kimya-otomatik; BacForge dersi)
    flag = "--nano-hq" if str(chemistry).lower().startswith("r10") else "--nano-raw"
    return ["flye", flag, str(long_reads), "-o", str(out_dir), "-t", str(threads)]


def unicycler_cmd(r1, r2, long_reads, out_dir, threads=8):
    return ["unicycler", "-1", str(r1), "-2", str(r2), "-l", str(long_reads),
            "-o", str(out_dir), "-t", str(threads)]


def medaka_consensus_cmd(long_reads, draft, out_dir, model="r1041_e82_400bps_sup_v5.0.0", threads=8):
    return ["medaka_consensus", "-i", str(long_reads), "-d", str(draft),
            "-o", str(out_dir), "-m", model, "-t", str(threads)]


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


def phabox_cmd(genome, out_dir, db, threads=8):
    return ["phabox2", "--task", "end_to_end", "--contigs", str(genome),
            "--outpth", str(out_dir), "--dbdir", str(db), "--threads", str(threads)]
