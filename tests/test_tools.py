from virusforge import tools


def test_fastp_cmd_has_io_and_json(tmp_path):
    cmd = tools.fastp_cmd("R1.fq", "R2.fq", tmp_path, threads=4)
    assert cmd[0] == "fastp" and "-w" in cmd and "4" in cmd
    assert any("fastp.json" in c for c in cmd)


def test_spades_careful():
    assert "--careful" in tools.spades_cmd("a", "b", "o")
    assert "--careful" not in tools.spades_cmd("a", "b", "o", careful=False)


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
