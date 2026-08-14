from pathlib import Path

from virusforge.modules.v12_lineage import parse_pangolin, parse_nextclade


def test_parse_pangolin(tmp_path):
    csv = tmp_path / "lineage_report.csv"
    csv.write_text(
        "taxon,lineage,conflict,ambiguity_score,scorpio_call,scorpio_support,"
        "scorpio_conflict,scorpio_notes,version,pangolin_version,scorpio_version,"
        "constellation_version,is_designated,qc_status,qc_notes,note\n"
        "sample,BA.2.86,0.0,,Omicron (BA.2-like),0.9,0.0,,PUSHER-v1.25,4.3.1,"
        "0.3.19,v0.1.12,True,pass,,Assigned from designation hash.\n")
    r = parse_pangolin(csv)
    assert r["lineage"] == "BA.2.86"
    assert r["scorpio_call"] == "Omicron (BA.2-like)"
    assert r["qc_status"] == "pass"
    assert r["pango_version"] == "4.3.1"
    assert "designation" in r["note"]


def test_parse_pangolin_missing_columns(tmp_path):
    csv = tmp_path / "min.csv"
    csv.write_text("taxon,lineage,qc_status\nsample,B.1.1.7,pass\n")
    r = parse_pangolin(csv)
    assert r["lineage"] == "B.1.1.7"
    assert r["scorpio_call"] == ""
    assert r["qc_status"] == "pass"


def test_parse_nextclade(tmp_path):
    tsv = tmp_path / "nextclade.tsv"
    tsv.write_text(
        "index\tseqName\tclade\tNextclade_pango\tqc.overallStatus\t"
        "totalSubstitutions\ttotalMissing\ttotalAminoacidSubstitutions\n"
        "0\tsample\t23I\tBA.2.86\tgood\t72\t305\t45\n")
    r = parse_nextclade(tsv)
    assert r["clade"] == "23I"
    assert r["nextclade_pango"] == "BA.2.86"
    assert r["qc_overall"] == "good"
    assert r["total_substitutions"] == 72
    assert r["total_missing"] == 305
    assert r["total_aa_substitutions"] == 45


def test_parse_nextclade_empty(tmp_path):
    tsv = tmp_path / "empty.tsv"
    tsv.write_text("index\tseqName\tclade\n")
    assert parse_nextclade(tsv) == {}
