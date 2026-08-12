import hashlib

import pytest

from virusforge import util
from tests.conftest import write_fastq


def test_sha256_known_value(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"virusforge")
    assert util.sha256(p) == hashlib.sha256(b"virusforge").hexdigest()


def test_find_short_reads(tmp_path):
    write_fastq(tmp_path / "s_R1.fastq")
    write_fastq(tmp_path / "s_R2.fastq")
    r1, r2 = util.find_short_reads(tmp_path)
    assert "r1" in r1.name.lower() and "r2" in r2.name.lower()


def test_find_long_reads_excludes_R1(tmp_path):
    # yalnız R1/R2 varsa long YOK (BacForge dersi: R1 de .fastq)
    write_fastq(tmp_path / "s_R1.fastq")
    write_fastq(tmp_path / "s_R2.fastq")
    assert util.find_long_reads(tmp_path) is None
    # ONT ipuçlu dosya eklenince onu seçer
    write_fastq(tmp_path / "sample_ont.fastq", length=5000)
    assert util.find_long_reads(tmp_path).name == "sample_ont.fastq"


def test_run_cmd_raises_on_failure(tmp_path):
    util.run_cmd(["true"])  # sorunsuz
    with pytest.raises(RuntimeError):
        util.run_cmd(["false"])
