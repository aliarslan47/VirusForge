"""Çoklu-örnek karşılaştırma (compare komutu) testleri."""
import json

from virusforge import tools


def test_blastn_local_and_makeblastdb_nucl_cmd():
    mk = tools.makeblastdb_nucl_cmd("all.fasta", "db")
    assert mk[0] == "makeblastdb" and "nucl" in mk
    bn = tools.blastn_local_cmd("all.fasta", "db", "out.tsv")
    assert bn[0] == "blastn" and "-remote" not in bn and "-outfmt" in bn


def test_parse_blastn_identity_length_weighted(tmp_path):
    from virusforge.compare import parse_blastn_identity
    p = tmp_path / "bn.tsv"
    # qseqid sseqid pident length — A→B iki hit (uzunluk-ağırlıklı ortalama)
    p.write_text("A\tB\t98\t1000\nA\tB\t90\t100\nA\tA\t100\t40000\n")
    pairs = parse_blastn_identity(p)
    assert abs(pairs[("A", "B")] - (98 * 1000 + 90 * 100) / 1100) < 0.01
    assert pairs[("A", "A")] == 100.0


def test_identity_matrix_symmetric_diag100():
    from virusforge.compare import identity_matrix
    labels = ["A", "B"]
    pairs = {("A", "B"): 97.0}
    m = identity_matrix(labels, pairs)
    assert m[0][0] == 100.0 and m[1][1] == 100.0
    assert m[0][1] == 97.0 and m[1][0] == 97.0   # simetrik doldurma


def _mkrun(base, name, seq="ACGT" * 10):
    r = base / name
    (r / "V03_POLISHING_VIRAL_QC" / "04_standardized").mkdir(parents=True)
    (r / "V03_POLISHING_VIRAL_QC" / "04_standardized" / "viral_genome.fasta").write_text(f">c\n{seq}\n")
    (r / "V04_VIRAL_IDENTIFICATION" / "04_standardized").mkdir(parents=True)
    (r / "V04_VIRAL_IDENTIFICATION" / "04_standardized" / "id.json").write_text(
        json.dumps({"taxonomy": "Viruses;Caudoviricetes;Autographiviridae"}))
    (r / "V09_COMPARATIVE_PHYLO" / "04_standardized").mkdir(parents=True)
    (r / "V09_COMPARATIVE_PHYLO" / "04_standardized" / "comparative.json").write_text(
        json.dumps({"ictv": {"genus": "Teseptimavirus", "species": "Teseptimavirus T7"}}))
    return r


def test_collect_samples(tmp_path):
    import json as _j  # noqa
    from virusforge.compare import collect_samples
    _mkrun(tmp_path, "runA")
    _mkrun(tmp_path, "runB", seq="TTTT" * 10)
    (tmp_path / "empty_run").mkdir()  # genomsuz → atlanmalı
    samples = collect_samples([tmp_path / "runA", tmp_path / "runB", tmp_path / "empty_run"])
    assert [s["name"] for s in samples] == ["runA", "runB"]
    assert samples[0]["length"] == 40 and samples[0]["ictv"]["genus"] == "Teseptimavirus"
    assert "Autographiviridae" in samples[0]["taxonomy"]


def test_build_combined_fasta(tmp_path):
    from virusforge.compare import collect_samples, build_combined_fasta
    _mkrun(tmp_path, "runA")
    samples = collect_samples([tmp_path / "runA"])
    out = tmp_path / "all.fasta"
    build_combined_fasta(samples, out)
    assert ">runA" in out.read_text()


def test_render_comparison_smoke():
    from virusforge.report.render import render_comparison
    data = {
        "samples": [{"name": "T7_hybrid", "length": 40532,
                     "ictv": {"genus": "Teseptimavirus", "species": "Teseptimavirus T7"},
                     "taxonomy": "Viruses;Caudoviricetes;Autographiviridae"}],
        "tree_newick": "(T7_hybrid:0.001,T7_short:0.001);",
        "matrix_labels": ["T7_hybrid", "T7_short"],
        "matrix": [[100.0, 99.5], [99.5, 100.0]],
    }
    h = render_comparison(data)
    assert "<!DOCTYPE html>" in h and 'charset="utf-8"' in h.lower()
    assert "T7_hybrid" in h and "Teseptimavirus" in h and "99.5" in h


def test_render_comparison_english():
    from virusforge.report.render import render_comparison
    data = {"samples": [{"name": "T7_hybrid", "length": 40532,
                         "ictv": {"genus": "Teseptimavirus", "species": "Teseptimavirus T7"},
                         "taxonomy": "Viruses;Caudoviricetes;Autographiviridae"}]}
    en = render_comparison(data, lang="en")
    tr = render_comparison(data, lang="tr")
    assert "Multi-Sample Comparison" in en and "<html lang='en'>" in en
    assert "Çoklu-Örnek Karşılaştırma" in tr and "Multi-Sample Comparison" not in tr


def test_run_compare_warns_under_two(tmp_path):
    from virusforge.compare import run_compare
    _mkrun(tmp_path, "runA")  # tek örnek
    out = run_compare([tmp_path / "runA"], tmp_path / "cmp", cfg={"general": {"threads": 1}})
    rep = out / "comparison_report.html"
    assert rep.exists() and '<!doctype html>' in rep.read_text().lower()
    data = json.loads((out / "comparison.json").read_text())
    assert data.get("warning")  # <2 genom → dürüst uyarı


def test_run_compare_writes_dual_language(tmp_path):
    # Çift-dilli: karşılaştırma da tr + en iki rapor üretir
    from virusforge.compare import run_compare
    _mkrun(tmp_path, "runA")
    out = run_compare([tmp_path / "runA"], tmp_path / "cmp", cfg={"general": {"threads": 1}})
    assert (out / "comparison_report.html").exists()
    en = out / "comparison_report_en.html"
    assert en.exists() and "Multi-Sample Comparison" in en.read_text()
