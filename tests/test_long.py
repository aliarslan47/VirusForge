"""Long-okuma yolu: izole conda_env sarmalayıcı (vf_long) — çalışan virusforge env korunur."""
from virusforge import tools


def test_long_cmds_wrap_conda_env():
    for cmd in (tools.nanoplot_cmd("r.fq", "out", conda_env="vf_long", conda_bin="conda"),
                tools.filtlong_cmd("r.fq", conda_env="vf_long", conda_bin="conda"),
                tools.flye_cmd("r.fq", "out", conda_env="vf_long", conda_bin="conda"),
                tools.medaka_consensus_cmd("r.fq", "d.fa", "out", conda_env="vf_long", conda_bin="conda")):
        assert cmd[:3] == ["conda", "run", "-n"]


def test_long_cmds_bare_without_env():
    assert tools.nanoplot_cmd("r.fq", "out")[0] == "NanoPlot"
    assert tools.filtlong_cmd("r.fq")[0] == "filtlong"
    assert tools.flye_cmd("r.fq", "out")[0] == "flye"
    assert tools.medaka_consensus_cmd("r.fq", "d.fa", "out")[0] == "medaka_consensus"


def test_flye_chemistry_flag():
    # R10 → --nano-hq, R9 → --nano-raw (kimya-otomatik)
    assert "--nano-hq" in tools.flye_cmd("r.fq", "out", chemistry="r10")
    assert "--nano-raw" in tools.flye_cmd("r.fq", "out", chemistry="r9")


def test_flye_uses_meta_for_viral():
    # küçük + ultra-yüksek kapsamlı viral genomlar için --meta şart
    # (T7 gerçek verisinde --meta olmadan "No disjointigs assembled" ile çöktü)
    assert "--meta" in tools.flye_cmd("r.fq", "out")
