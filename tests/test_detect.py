from virusforge import detect
from tests.conftest import write_fasta, write_fastq


def test_detect_short(tmp_path):
    write_fastq(tmp_path / "s_R1.fastq", length=150)
    write_fastq(tmp_path / "s_R2.fastq", length=150)
    assert detect.detect_mode(tmp_path)["mode"] == detect.SHORT_READ


def test_detect_long(tmp_path):
    write_fastq(tmp_path / "reads_ont.fastq", length=5000)
    assert detect.detect_mode(tmp_path)["mode"] == detect.LONG_READ


def test_detect_hybrid(tmp_path):
    write_fastq(tmp_path / "s_R1.fastq", length=150)
    write_fastq(tmp_path / "s_R2.fastq", length=150)
    write_fastq(tmp_path / "reads_ont.fastq", length=5000)
    assert detect.detect_mode(tmp_path)["mode"] == detect.HYBRID


def test_detect_assembly(tmp_path):
    write_fasta(tmp_path / "genome.fasta")
    assert detect.detect_mode(tmp_path)["mode"] == detect.ASSEMBLY_INPUT


def test_config_override_wins(tmp_path):
    write_fastq(tmp_path / "s_R1.fastq", length=150)
    write_fastq(tmp_path / "s_R2.fastq", length=150)
    cfg = {"general": {"mode": "long"}}
    assert detect.detect_mode(tmp_path, cfg)["mode"] == detect.LONG_READ
