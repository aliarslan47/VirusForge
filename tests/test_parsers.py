"""V01/V03/V04/V05/V06/V07 parser'ları — gerçek tool çıktı fixture'larıyla."""
import json

from virusforge.modules.v01_qc import parse_fastp_json, parse_nanoplot
from virusforge.modules.v03_polish_qc import parse_checkv, parse_quast
from virusforge.modules.v04_identify import parse_genomad
from virusforge.modules.v05_taxonomy import parse_mash
from virusforge.modules.v06_annotate import parse_pharokka
from virusforge.modules.v07_phage_char import parse_phabox


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


def test_parse_cds_genes_from_merged_tsv(tmp_path):
    from virusforge.modules.v06_annotate import parse_cds_genes
    p = tmp_path / "pharokka_cds_final_merged_output.tsv"
    p.write_text(
        "gene\tstart\tstop\tstrand\tphrog\tMethod\tannot\tcategory\n"
        "X_CDS_0001\t891\t1\t-\t1339\tPHANOTATE\tinternal virion protein\thead and packaging\n"
        "X_CDS_0002\t4374\t1990\t+\t457\tPHANOTATE\ttail protein\ttail\n")
    genes = parse_cds_genes(p)
    assert len(genes) == 2
    assert genes[0] == {"gene": "X_CDS_0001", "start": "891", "stop": "1", "strand": "-",
                        "product": "internal virion protein", "phrog": "1339",
                        "category": "head and packaging"}
    assert genes[1]["product"] == "tail protein" and genes[1]["strand"] == "+"


def test_parse_samtools_depth_breadth_and_mean(tmp_path):
    from virusforge.modules.v03_polish_qc import parse_samtools_depth
    # ref pos depth — 5 pozisyon, 4'ü kapsanmış (>=1), biri 0
    p = tmp_path / "depth.tsv"
    p.write_text("NC\t1\t10\nNC\t2\t20\nNC\t3\t0\nNC\t4\t30\nNC\t5\t40\n")
    m = parse_samtools_depth(p)
    assert m["positions"] == 5 and m["covered_bases"] == 4
    assert m["breadth_pct"] == 80.0                       # 4/5
    assert m["mean_depth"] == 20.0                        # (10+20+0+30+40)/5


def test_parse_vadr_pass_fail_alerts(tmp_path):
    from virusforge.modules.v06_annotate import parse_vadr
    d = tmp_path / "vout"
    d.mkdir()
    (d / "vout.vadr.pass.list").write_text("#comment\nseq1\n")
    (d / "vout.vadr.fail.list").write_text("#comment\n")            # boş → fail yok
    (d / "vout.vadr.alt.list").write_text("#idx\tseq\tcode\tdesc\n1\tseq1\tambgnt5s\tN at start\n")
    m = parse_vadr(d)
    assert m["n_pass"] == 1 and m["n_fail"] == 0 and m["pass"] is True
    assert m["n_alerts"] == 1


def test_parse_vadr_fail_when_fail_list_nonempty(tmp_path):
    from virusforge.modules.v06_annotate import parse_vadr
    d = tmp_path / "vout"
    d.mkdir()
    (d / "vout.vadr.pass.list").write_text("")
    (d / "vout.vadr.fail.list").write_text("seqX\n")
    m = parse_vadr(d)
    assert m["n_fail"] == 1 and m["pass"] is False


def test_parse_phabox(tmp_path):
    (tmp_path / "phatyp_prediction.tsv").write_text("Accession\tTYPE\tScore\nc1\ttemperate\t0.9\n")
    m = parse_phabox(tmp_path)
    assert m["lifestyle"]["TYPE"] == "temperate"
