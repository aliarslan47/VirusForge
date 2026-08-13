from virusforge import tools


def test_fastp_cmd_has_io_and_json(tmp_path):
    cmd = tools.fastp_cmd("R1.fq", "R2.fq", tmp_path, threads=4)
    assert cmd[0] == "fastp" and "-w" in cmd and "4" in cmd
    assert any("fastp.json" in c for c in cmd)


def test_spades_careful():
    assert "--careful" in tools.spades_cmd("a", "b", "o")
    assert "--careful" not in tools.spades_cmd("a", "b", "o", careful=False)


# ---- RNA-virüs yolu (M2-B Faz 1) araç komutları ----

def test_rnaviralspades_cmd():
    cmd = tools.rnaviralspades_cmd("R1.fq", "R2.fq", "out", threads=4)
    assert cmd[0] == "spades.py" and "--rnaviral" in cmd
    assert "-1" in cmd and "-2" in cmd and "R1.fq" in cmd and "out" in cmd


def test_minimap2_cmd_short_preset_and_conda():
    cmd = tools.minimap2_cmd("ref.fa", ["r1.fq", "r2.fq"], threads=4,
                             conda_env="vf_rna", conda_bin="conda")
    assert cmd[:4] == ["conda", "run", "-n", "vf_rna"]
    assert "minimap2" in cmd and "-ax" in cmd and "sr" in cmd
    assert "ref.fa" in cmd and "r1.fq" in cmd and "r2.fq" in cmd


def test_samtools_sort_index_depth_cmd():
    s = tools.samtools_sort_cmd("in.sam", "out.bam", threads=2, conda_env="vf_rna")
    assert s[:4] == ["conda", "run", "-n", "vf_rna"] and "sort" in s and "out.bam" in s
    i = tools.samtools_index_cmd("out.bam", conda_env="vf_rna")
    assert "index" in i and "out.bam" in i
    d = tools.samtools_depth_cmd("out.bam", conda_env="vf_rna")
    assert "depth" in d and "-a" in d and "out.bam" in d   # -a = tüm pozisyonlar (breadth için)


def test_samtools_mpileup_and_ivar_consensus_stream():
    # pipe: mpileup | ivar consensus — conda run --no-capture-output (stdout tamponlanmasın)
    mp = tools.samtools_mpileup_cmd("ref.fa", "s.bam", conda_env="vf_rna")
    assert "mpileup" in mp and "ref.fa" in mp and "s.bam" in mp and "--no-capture-output" in mp
    ic = tools.ivar_consensus_cmd("cons", min_depth=10, min_freq=0.5, conda_env="vf_rna")
    assert "ivar" in ic and "consensus" in ic and "cons" in ic and "--no-capture-output" in ic
    assert "10" in ic and "0.5" in ic


def test_ivar_trim_cmd():
    t = tools.ivar_trim_cmd("in.bam", "primers.bed", "trimmed", conda_env="vf_rna")
    assert t[:4] == ["conda", "run", "-n", "vf_rna"]
    assert "ivar" in t and "trim" in t and "primers.bed" in t and "trimmed" in t


def test_vadr_cmd():
    v = tools.vadr_cmd("genome.fa", "vout", "databases/vadr", "sarscov2", conda_env="vf_vadr")
    assert v[:4] == ["conda", "run", "-n", "vf_vadr"]
    assert "v-annotate.pl" in v and "--mdir" in v and "--mkey" in v and "sarscov2" in v


def test_flye_hq_for_r10():
    assert "--nano-hq" in tools.flye_cmd("l", "o", "r10")


def test_flye_raw_for_r9():
    assert "--nano-raw" in tools.flye_cmd("l", "o", "r9")


def test_unicycler_has_long():
    cmd = tools.unicycler_cmd("r1", "r2", "long", "o")
    assert "-l" in cmd and "long" in cmd


def test_genomad_and_checkv_and_pharokka_and_phabox():
    assert tools.genomad_cmd("g", "o", "db")[:2] == ["genomad", "end-to-end"]
    assert tools.checkv_cmd("g", "o", "db")[:2] == ["checkv", "end_to_end"]
    assert tools.pharokka_cmd("g", "o", "db")[0] == "pharokka.py"
    assert "--task" in tools.phabox_cmd("g", "o", "db")
    assert tools.mash_dist_cmd("s", "q")[:2] == ["mash", "dist"]
