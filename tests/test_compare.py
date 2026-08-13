"""Çoklu-örnek karşılaştırma (compare komutu) testleri."""
from virusforge import tools


def test_blastn_local_and_makeblastdb_nucl_cmd():
    mk = tools.makeblastdb_nucl_cmd("all.fasta", "db")
    assert mk[0] == "makeblastdb" and "nucl" in mk
    bn = tools.blastn_local_cmd("all.fasta", "db", "out.tsv")
    assert bn[0] == "blastn" and "-remote" not in bn and "-outfmt" in bn
