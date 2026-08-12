"""V01/V04/V05/V06/V07/V08 parser'ları — gerçek tool çıktı fixture'larıyla."""
import json

from virusforge.modules.v01_qc import parse_fastp_json, parse_nanoplot
from virusforge.modules.v04_polish_qc import parse_checkv, parse_quast
from virusforge.modules.v05_identify import parse_genomad
from virusforge.modules.v06_taxonomy import parse_mash
from virusforge.modules.v07_annotate import parse_pharokka
from virusforge.modules.v08_phage_char import parse_phabox


def test_parse_fastp_json(tmp_path):
    p = tmp_path / "fastp.json"
    p.write_text(json.dumps({"summary": {
        "before_filtering": {"total_reads": 1000},
        "after_filtering": {"total_reads": 900, "q30_rate": 0.95, "gc_content": 0.4}}}))
    m = parse_fastp_json(p)
    assert m["raw_reads"] == 1000 and m["clean_reads"] == 900 and m["q30_rate"] == 0.95


def test_parse_nanoplot(tmp_path):
    p = tmp_path / "NanoStats.txt"
    p.write_text("Mean read length:\t5,000.0\nRead length N50:\t8,000.0\n"
                 "Mean read quality:\t12.5\nNumber of reads:\t10,000.0\n")
    m = parse_nanoplot(p)
    assert m["mean_len"] == 5000.0 and m["read_n50"] == 8000.0 and m["mean_qual"] == 12.5


def test_parse_quast(tmp_path):
    p = tmp_path / "report.tsv"
    p.write_text("Assembly\tg\nTotal length\t45000\n# contigs\t1\nN50\t45000\nGC (%)\t40.5\n")
    m = parse_quast(p)
    assert m["total_length"] == 45000 and m["contigs"] == 1 and m["gc"] == 40.5


def test_parse_checkv(tmp_path):
    p = tmp_path / "quality_summary.tsv"
    p.write_text("contig_id\tcontig_length\tcompleteness\tcontamination\tcheckv_quality\n"
                 "c1\t45000\t99.5\t0.0\tComplete\n")
    m = parse_checkv(p)
    assert m["contig_length"] == 45000 and m["completeness"] == "99.5"
    assert m["checkv_quality"] == "Complete"


def test_parse_genomad(tmp_path):
    p = tmp_path / "vs.tsv"
    p.write_text("seq_name\tvirus_score\ttaxonomy\nc1\t0.99\tViruses;Duplodnaviria;Caudoviricetes\n")
    m = parse_genomad(p)
    assert m["is_viral"] and m["top_score"] == 0.99 and "Caudoviricetes" in m["taxonomy"]


def test_parse_mash_dedup_by_accession(tmp_path):
    p = tmp_path / "dist.tsv"
    p.write_text(
        "refs/MK448231.1_x.fna\tq\t0.02\t0\t900/1000\n"
        "refs/MK448231.1_copy.fna\tq\t0.05\t0\t800/1000\n"   # aynı accession → dedup
        "refs/GCF_000000001.1_y.fna\tq\t0.03\t0\t850/1000\n")
    hits = parse_mash(p)
    assert len(hits) == 2                       # dedup çalıştı
    assert hits[0]["accession"] == "MK448231.1"  # en düşük mesafe önde
    assert hits[0]["mash_dist"] == 0.02


def test_parse_pharokka_sums_across_contigs(tmp_path):
    # gerçek format: Description<TAB>Count<TAB>contig, contig başına satır
    p = tmp_path / "pharokka_cds_functions.tsv"
    p.write_text("Description\tCount\tcontig\n"
                 "CDS\t60\tNODE_1\ntRNAs\t2\tNODE_1\ntail\t5\tNODE_1\n"
                 "CDS\t2\tNODE_2\n")
    m = parse_pharokka(p)
    assert m["cds"] == 62          # 60 + 2 toplandı (son satır DEĞİL)
    assert m["trna"] == 2 and m["functions"]["tail"] == 5


def test_parse_phabox(tmp_path):
    (tmp_path / "phatyp_prediction.tsv").write_text("Accession\tTYPE\tScore\nc1\ttemperate\t0.9\n")
    m = parse_phabox(tmp_path)
    assert m["lifestyle"]["TYPE"] == "temperate"
