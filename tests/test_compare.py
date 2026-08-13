"""Çoklu-örnek karşılaştırma (compare komutu) testleri."""
import json

from virusforge import tools


def test_blastn_local_and_makeblastdb_nucl_cmd():
    mk = tools.makeblastdb_nucl_cmd("all.fasta", "db")
    assert mk[0] == "makeblastdb" and "nucl" in mk
    bn = tools.blastn_local_cmd("all.fasta", "db", "out.tsv")
    assert bn[0] == "blastn" and "-remote" not in bn and "-outfmt" in bn


def test_clinker_cmd_builds_plot_and_conda_wrap():
    # clinker <gbk...> -p out.html ; conda env verilince `conda run -n <env>` ile sarılır
    cmd = tools.clinker_cmd(["a.gbk", "b.gbk"], "clinker.html", conda_env="ali-clinker")
    assert cmd[:4] == ["conda", "run", "-n", "ali-clinker"]
    assert "clinker" in cmd and "a.gbk" in cmd and "b.gbk" in cmd
    assert cmd[-2:] == ["-p", "clinker.html"]
    # env yoksa ham komut (conda run yok)
    bare = tools.clinker_cmd(["a.gbk", "b.gbk"], "clinker.html")
    assert bare[0] == "clinker" and "run" not in bare


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


# ---- clinker interaktif synteny (M3 Faz 2) ----

def _add_gbk(run_dir, text="LOCUS x\n//\n"):
    p = run_dir / "V06_GENOME_ANNOTATION" / "03_native_outputs" / "pharokka"
    p.mkdir(parents=True, exist_ok=True)
    (p / "pharokka.gbk").write_text(text)


def test_stage_genbanks_names_by_sample_and_skips_missing(tmp_path):
    from virusforge.compare import stage_genbanks
    a = _mkrun(tmp_path, "runA"); _add_gbk(a)
    b = _mkrun(tmp_path, "runB")  # gbk YOK → skipped
    work = tmp_path / "work"
    staged, skipped = stage_genbanks([a, b], work)
    assert [p.name for p in staged] == ["runA.gbk"]  # örnek-adıyla evrilir
    assert "runB" in skipped                          # eksik dürüstçe bildirilir


def test_build_clinker_none_under_two_genomes(tmp_path):
    # <2 anotasyonlu genom → clinker atlanır (None), sessiz hata yok
    from virusforge.compare import build_clinker
    a = _mkrun(tmp_path, "runA"); _add_gbk(a)
    b = _mkrun(tmp_path, "runB")  # gbk yok
    assert build_clinker([a, b], tmp_path / "cmp", cfg={"general": {"threads": 1}}) is None


def test_render_comparison_links_clinker():
    from virusforge.report.render import render_comparison
    data = {"samples": [{"name": "T7_a", "length": 40000},
                        {"name": "T7_b", "length": 40000}],
            "clinker": {"html": "clinker.html", "n_genomes": 2, "skipped": []}}
    tr = render_comparison(data, lang="tr")
    en = render_comparison(data, lang="en")
    assert "clinker.html" in tr and "clinker" in tr.lower()
    assert "clinker.html" in en and "clinker" in en.lower()
