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
