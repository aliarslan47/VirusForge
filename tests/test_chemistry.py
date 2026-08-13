"""Kaliteye-dayalı ONT kimya tespiti (R9 --nano-raw vs R10 --nano-hq)."""
from virusforge.modules.v02_assembly import resolve_chemistry


def test_low_quality_reads_use_r9():
    # Q < eşik → yüksek hata → --nano-raw (R9); Flye --nano-hq bu veride çöker
    assert resolve_chemistry(10.4) == "r9"
    assert resolve_chemistry(12.0) == "r9"


def test_high_quality_reads_use_r10():
    assert resolve_chemistry(15.0) == "r10"
    assert resolve_chemistry(20.0) == "r10"


def test_unknown_quality_defaults_r10():
    # kalite bilinmiyorsa modern ONT varsayılanı
    assert resolve_chemistry(None) == "r10"
