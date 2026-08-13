import pytest

from virusforge.modules.v02_assembly import select_assembler

_CFG = {"general": {"threads": 4},
        "tools": {"flye": {"chemistry": "r10"}, "spades": {"careful": True}}}


def test_short_selects_spades(tmp_path):
    cmd, contig = select_assembler("SHORT_READ", {"r1": "a", "r2": "b"}, tmp_path, _CFG)
    assert cmd[0] == "spades.py"
    assert str(contig).endswith("contigs.fasta")


def test_hybrid_selects_unicycler(tmp_path):
    cmd, _ = select_assembler("HYBRID", {"r1": "a", "r2": "b", "long": "l"}, tmp_path, _CFG)
    assert cmd[0] == "unicycler"


def test_long_selects_flye_with_chem(tmp_path):
    cmd, _ = select_assembler("LONG_READ", {"long": "l"}, tmp_path, _CFG)
    assert cmd[0] == "flye" and "--nano-hq" in cmd


def test_missing_long_raises(tmp_path):
    with pytest.raises(ValueError):
        select_assembler("LONG_READ", {"r1": "a"}, tmp_path, _CFG)
