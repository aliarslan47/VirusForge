"""Çoklu-örnek karşılaştırma (compare komutu) testleri."""
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
