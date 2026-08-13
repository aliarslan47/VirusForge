"""Sayısal contig header temizleme — Unicycler '>1' adlandırması PhaBOX'ı çökertiyor
(pandas 'merge on object and int64 for Accession'). Gerçek T7 hibrit doğrulamasında bulundu."""
from virusforge.modules.v02_assembly import sanitize_contig_names


def test_numeric_headers_get_prefixed(tmp_path):
    fa = tmp_path / "in.fasta"
    fa.write_text(">1\nAAAA\n>2\nCCCC\n")
    out = tmp_path / "out.fasta"
    sanitize_contig_names(fa, out)
    txt = out.read_text()
    assert ">contig_1" in txt and ">contig_2" in txt
    assert ">1\n" not in txt


def test_nonnumeric_headers_unchanged(tmp_path):
    fa = tmp_path / "in.fasta"
    fa.write_text(">NODE_1_length_45\nAAAA\n>contig_3\nCCCC\n")
    out = tmp_path / "out.fasta"
    sanitize_contig_names(fa, out)
    txt = out.read_text()
    assert ">NODE_1_length_45" in txt and ">contig_3" in txt
