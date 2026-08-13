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


# --------------------------------------------------------------------------- #
# parse_blast_hits — tür-dedup top-N
# --------------------------------------------------------------------------- #
def test_parse_blast_hits_dedup_species_topn(tmp_path):
    from virusforge.modules.v09_comparative import parse_blast_hits
    p = tmp_path / "blast.tsv"
    # sacc staxids sscinames pident qcovs length evalue bitscore
    p.write_text(
        "V01146\t10760\tEscherichia virus T7\t99.9\t98\t39000\t0\t7200\n"
        "NC_XXX\t10760\tEscherichia virus T7\t99.0\t97\t38000\t0\t7000\n"   # aynı tür → tekille
        "EU734174\t347326\tEnterobacteria phage 13a\t95.6\t90\t35000\t0\t5000\n"
        "JQ965703\t999\tPhage X\t95.4\t88\t34000\t0\t4800\n")
    hits = parse_blast_hits(p, n=5)
    assert [h["species"] for h in hits] == ["Escherichia virus T7", "Enterobacteria phage 13a", "Phage X"]
    assert hits[0]["accession"] == "V01146" and hits[0]["identity"] == "99.9"


# --------------------------------------------------------------------------- #
# parse_iqtree + parse_taxmyphage
# --------------------------------------------------------------------------- #
def test_parse_iqtree_newick(tmp_path):
    from virusforge.modules.v09_comparative import parse_iqtree
    t = tmp_path / "x.treefile"
    t.write_text("(sample:0.001,(V01146:0.002,EU734174:0.04)95:0.01);\n")
    m = parse_iqtree(t)
    assert m["newick"].startswith("(") and "V01146" in m["newick"]


def test_parse_taxmyphage(tmp_path):
    from virusforge.modules.v09_comparative import parse_taxmyphage
    (tmp_path / "Summary_taxonomy.tsv").write_text(
        "Genome\tGenus\tSpecies\nsample\tTeseptimavirus\tEscherichia virus T7\n")
    m = parse_taxmyphage(tmp_path)
    assert m["genus"] == "Teseptimavirus" and m["species"] == "Escherichia virus T7"
