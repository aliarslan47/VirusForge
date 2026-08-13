"""Araç sürüm çıktısından temiz sürüm token'ı ayrıştırma (uyarı/yardım gürültüsünü atla).
Rapordaki 'QUAST WARNING: Python locale…' / 'CheckV Usage:…' çöpü bu yüzden çıkıyordu."""
from virusforge.registry import _parse_version


def test_clean_version_tokens():
    assert _parse_version("fastp 1.3.6") == "1.3.6"
    assert _parse_version("geNomad, version 1.12.0") == "1.12.0"
    assert _parse_version("SPAdes genome assembler v4.3.0") == "v4.3.0"
    assert _parse_version("Mash 2.3") == "2.3"
    assert _parse_version("Pharokka 1.9.1") == "1.9.1"


def test_skips_warning_and_usage_noise():
    # QUAST önce locale uyarısı basar, sonra sürüm
    assert _parse_version("WARNING: Python locale settings can't be changed\nQUAST v5.3.0") == "v5.3.0"
    # sürümü olmayan yardım/usage metni → None (çöp gösterme)
    assert _parse_version("Usage: checkv [OPTIONS] COMMAND [ARGS]...") is None
    assert _parse_version("usage: phabox2 [-h] [--task TASK]") is None
    assert _parse_version("") is None
