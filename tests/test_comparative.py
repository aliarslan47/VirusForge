"""M3 comparative modülü testleri: araç komutları + parser'lar + modül koşumu."""
from virusforge import tools


# --------------------------------------------------------------------------- #
# Araç komut kurucuları
# --------------------------------------------------------------------------- #
def test_blastn_remote_cmd():
    c = tools.blastn_remote_cmd("q.fasta", "o.tsv", db="ref_viruses_rep_genomes", max_target_seqs=50)
    assert c[0] == "blastn" and "-remote" in c and "ref_viruses_rep_genomes" in c
    assert "-outfmt" in c


def test_efetch_cmd():
    c = tools.efetch_cmd("V01146", "out.fasta")
    assert c[0] == "efetch" and "V01146" in c and "fasta" in c


def test_mafft_and_iqtree_cmd():
    assert tools.mafft_cmd("in.fa", "out.aln")[0] == "mafft"
    ic = tools.iqtree_cmd("out.aln", "pfx")
    assert ic[0] in ("iqtree2", "iqtree") and "-s" in ic


def test_taxmyphage_cmd():
    assert tools.taxmyphage_cmd("g.fa", "out")[0] == "taxmyphage"
