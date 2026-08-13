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


def test_run_pipe_streams_cmd1_into_cmd2(tmp_path):
    # cmd1 stdout → cmd2 stdin; cmd2 stdout → out_path (samtools mpileup | ivar consensus deseni)
    out = tmp_path / "piped.txt"
    util.run_pipe(["printf", "b\\na\\nc\\n"], ["sort"], out, tmp_path / "log.txt")
    assert out.read_text() == "a\nb\nc\n"


def test_run_pipe_raises_when_second_fails(tmp_path):
    with pytest.raises(RuntimeError):
        util.run_pipe(["printf", "x"], ["false"], tmp_path / "o.txt", tmp_path / "l.txt")


def test_run_pipe_raises_on_missing_tool(tmp_path):
    with pytest.raises(RuntimeError):
        util.run_pipe(["printf", "x"], ["no_such_tool_xyz"], tmp_path / "o.txt", tmp_path / "l.txt")
