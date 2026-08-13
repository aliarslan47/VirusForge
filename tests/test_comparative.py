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


def test_blastp_and_makeblastdb_cmd():
    mk = tools.makeblastdb_prot_cmd("ref.faa", "refdb")
    assert mk[0] == "makeblastdb" and "prot" in mk
    bp = tools.blastp_cmd("q.faa", "refdb", "out.tsv")
    assert bp[0] == "blastp" and "-outfmt" in bp


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
def test_mash_sketch_indiv_and_dist_table_cmd():
    sk = tools.mash_sketch_indiv_cmd("seqs.fasta", "msk")
    assert sk[:2] == ["mash", "sketch"] and "-i" in sk and "seqs.fasta" in sk
    dt = tools.mash_dist_table_cmd("msk.msh")
    assert dt[:2] == ["mash", "dist"] and "-t" in dt and dt.count("msk.msh") == 2


def test_parse_mash_square_table():
    from virusforge.modules.v09_comparative import parse_mash_square
    txt = "#query\tsample\tV01146.1\tEU734174.1\n" \
          "sample\t0\t0.001\t0.04\n" \
          "V01146.1\t0.001\t0\t0.041\n" \
          "EU734174.1\t0.04\t0.041\t0\n"
    labels, matrix = parse_mash_square(txt)
    assert labels == ["sample", "V01146.1", "EU734174.1"]        # başlıklar ilk token
    assert matrix[0][1] == 0.001 and matrix[2][1] == 0.041       # simetrik değerler


def test_mash_nj_newick_has_taxa():
    from virusforge.modules.v09_comparative import mash_nj_newick
    labels = ["sample", "V01146", "EU734174"]
    matrix = [[0, 0.001, 0.04], [0.001, 0, 0.041], [0.04, 0.041, 0]]
    nwk = mash_nj_newick(labels, matrix)
    assert nwk.strip().endswith(";") and "sample" in nwk and "V01146" in nwk


def test_build_mash_tree_real(tmp_path):
    # gerçek mash + biopython NJ: 3 dizilik fasta → newick (etiketler korunur)
    from virusforge.modules.v09_comparative import build_mash_tree
    fa = tmp_path / "seqs.fasta"
    fa.write_text(">sample\n" + "ACGT" * 40 + "\n"
                  ">V01146.1 T7\n" + "ACGT" * 39 + "ACGA\n"
                  ">EU734174.1 13a\n" + "TTGGCCAA" * 20 + "\n")
    nwk = build_mash_tree(fa, tmp_path / "work")
    assert nwk and "sample" in nwk and "V01146.1" in nwk and nwk.strip().endswith(";")


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


# --------------------------------------------------------------------------- #
# V09Comparative modül koşumu (araçsız/ağsız → dürüst WARNING / N/A)
# --------------------------------------------------------------------------- #
def test_parse_pharokka_gff_genes(tmp_path):
    from virusforge.modules.v09_comparative import parse_pharokka_gff
    p = tmp_path / "pharokka.gff"
    p.write_text(
        "##gff-version 3\n"
        "contig_1\tPHANOTATE\tCDS\t1\t891\t-66027\t-\t0\tID=x;locus_tag=CDS_0001;function=head and packaging;product=y\n"
        "contig_1\tPHANOTATE\tCDS\t900\t1500\t-10\t+\t0\tID=z;locus_tag=CDS_0002;function=tail;product=w\n")
    genes = parse_pharokka_gff(p)
    assert len(genes) == 2
    assert genes[0] == {"gene": "CDS_0001", "start": 1, "end": 891, "strand": "-", "function": "head and packaging"}
    assert genes[1]["function"] == "tail" and genes[1]["strand"] == "+"


def test_parse_blastp_pairs_best_hit(tmp_path):
    from virusforge.modules.v09_comparative import parse_blastp_pairs
    p = tmp_path / "bp.tsv"
    # qseqid sseqid pident bitscore
    p.write_text("CDS_0001\tREF_01\t99\t500\nCDS_0001\tREF_02\t80\t300\nCDS_0002\tREF_05\t95\t400\n")
    pairs = parse_blastp_pairs(p)
    assert pairs["CDS_0001"] == "REF_01" and pairs["CDS_0002"] == "REF_05"  # en yüksek bitscore


def test_copy_viridic_heatmap(tmp_path):
    from virusforge.modules.v09_comparative import _copy_viridic_heatmap
    tout = tmp_path / "taxmyphage" / "Results_per_genome" / "contig_1"
    tout.mkdir(parents=True)
    (tout / "heatmap.png").write_bytes(b"\x89PNG\r\n")
    viz = tmp_path / "viz"
    viz.mkdir()
    ok = _copy_viridic_heatmap(tmp_path / "taxmyphage", viz)
    assert ok and (viz / "viridic_heatmap.png").exists()


def test_copy_viridic_heatmap_missing(tmp_path):
    from virusforge.modules.v09_comparative import _copy_viridic_heatmap
    (tmp_path / "empty").mkdir()
    assert _copy_viridic_heatmap(tmp_path / "empty", tmp_path) is False


def test_v05_fallback_hits_uses_closest_when_blast_empty():
    from virusforge.modules.v09_comparative import _v05_fallback_hits
    from virusforge.module import Context
    c = Context(sample_dir=".", run_dir=".", cfg={}, mode="SHORT_READ")
    c.results["V05"] = {"closest_10": [{"accession": "V01146", "mash_dist": 0.001},
                                       {"accession": "EU734174", "mash_dist": 0.04}]}
    hits = _v05_fallback_hits(c, 5)
    assert hits[0]["accession"] == "V01146" and hits[0]["species"] == "V01146"
    assert len(hits) == 2


def test_v09_not_applicable_when_not_viral(tmp_path):
    from virusforge.module import Context, Status
    from virusforge.modules.v09_comparative import V09Comparative
    from tests.conftest import write_fasta
    c = Context(sample_dir=tmp_path, run_dir=tmp_path / "run", cfg={}, mode="SHORT_READ")
    (tmp_path / "run").mkdir()
    c.results["V04"] = {"is_viral": False}
    c.artifacts["V03"] = {"genome": str(write_fasta(tmp_path / "g.fasta"))}
    res = V09Comparative().run(c)
    assert res.status == Status.NOT_APPLICABLE


def test_v09_warning_when_offline_or_no_tool(tmp_path, monkeypatch):
    # harici blast/efetch çağrılarını no-op yap (birim testi ağ VURMAZ)
    import subprocess
    from virusforge import util
    from virusforge.module import Context, Status
    from virusforge.modules.v09_comparative import V09Comparative
    from tests.conftest import write_fasta
    monkeypatch.setattr(util, "run_cmd", lambda *a, **k: subprocess.CompletedProcess([], 0, "", ""))
    monkeypatch.setattr(util, "run_redirect", lambda *a, **k: None)
    c = Context(sample_dir=tmp_path, run_dir=tmp_path / "run", cfg={}, mode="SHORT_READ")
    (tmp_path / "run").mkdir()
    c.results["V04"] = {"is_viral": True}
    c.artifacts["V03"] = {"genome": str(write_fasta(tmp_path / "g.fasta"))}
    res = V09Comparative().run(c)
    assert res.status == Status.WARNING     # blast çıktısı yok → yeterli hit yok → dürüst WARNING
    d = c.run_dir / "V09_COMPARATIVE_PHYLO"
    assert (d / "V09_summary.json").exists() and (d / "01_input").is_dir()
    assert (d / "04_standardized" / "comparative.json").exists()
