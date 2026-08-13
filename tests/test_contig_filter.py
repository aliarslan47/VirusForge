"""Flye çıktısındaki düşük-kapsamlı junk contig'lerin elenmesi (gerçek T7 long doğrulamasında bulundu:
ana faj 1911x, junk 3-22x → junk downstream'i kirletiyor: sahte AMR, yanlış yaşam tarzı)."""
from virusforge.modules.v02_assembly import filter_contigs_by_coverage


def test_drops_low_coverage_junk(tmp_path):
    info = tmp_path / "assembly_info.txt"
    info.write_text("#seq_name\tlength\tcov.\tcirc.\n"
                    "contig_3\t38623\t1911\tY\n"
                    "contig_2\t17456\t3\tN\n"
                    "contig_1\t8715\t8\tN\n"
                    "contig_5\t5480\t22\tY\n")
    fa = tmp_path / "in.fasta"
    fa.write_text(">contig_3\nAAAA\n>contig_2\nCCCC\n>contig_1\nGGGG\n>contig_5\nTTTT\n")
    out = tmp_path / "out.fasta"
    kept = filter_contigs_by_coverage(info, fa, out, min_frac=0.1)
    assert kept == ["contig_3"]          # 3/8/22 << 191 eşiği → atıldı
    txt = out.read_text()
    assert ">contig_3" in txt and ">contig_2" not in txt and ">contig_5" not in txt


def test_keeps_all_similar_coverage(tmp_path):
    # meşru çoklu-contig (benzer kapsam) korunur
    info = tmp_path / "assembly_info.txt"
    info.write_text("#seq_name\tlength\tcov.\nc1\t40000\t100\nc2\t20000\t90\n")
    fa = tmp_path / "in.fasta"
    fa.write_text(">c1\nAAAA\n>c2\nCCCC\n")
    out = tmp_path / "out.fasta"
    kept = filter_contigs_by_coverage(info, fa, out, min_frac=0.1)
    assert set(kept) == {"c1", "c2"}
