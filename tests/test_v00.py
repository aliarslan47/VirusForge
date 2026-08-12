import json

from virusforge import config
from virusforge.module import Context, Status
from virusforge.modules.v00_input import V00Input
from tests.conftest import write_fastq


def test_v00_runs_short(tmp_path):
    sample = tmp_path / "sample"
    sample.mkdir()
    write_fastq(sample / "s_R1.fastq", length=150)
    write_fastq(sample / "s_R2.fastq", length=150)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ctx = Context(sample_dir=sample, run_dir=run_dir, cfg=config.load_config())

    res = V00Input().run(ctx)

    assert res.status == Status.PASS
    assert ctx.mode == "SHORT_READ"
    base = run_dir / "V00_INPUT_AUTO_DETECTION"
    dt = json.loads((base / "04_standardized" / "data_type.json").read_text())
    assert dt["mode"] == "SHORT_READ"
    assert (base / "05_statistics" / "read_statistics.tsv").exists()
    assert (base / "08_metadata" / "checksums.sha256").exists()
    assert (base / "V00_summary.json").exists()
