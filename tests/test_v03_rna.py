"""V03 RNA QC: CheckV yerine referans kapsama (BAM'den samtools depth)."""
from pathlib import Path

from virusforge.module import Context
from virusforge.modules.v03_polish_qc import V03PolishQC
from virusforge import util


def test_v03_rna_computes_coverage_not_checkv(tmp_path, monkeypatch):
    draft = tmp_path / "draft.fa"
    draft.write_text(">NC\n" + "ACGT" * 10 + "\n")
    bam = tmp_path / "aln.bam"
    bam.write_text("bam")
    run = tmp_path / "run"
    run.mkdir()
    cfg = {"general": {"molecule": "rna", "threads": 2}, "tools": {"rna": {"conda_env": "vf_rna"}}}
    ctx = Context(sample_dir=tmp_path, run_dir=run, cfg=cfg, mode="SHORT_READ")
    ctx.artifacts["V02"] = {"draft": str(draft), "bam": str(bam)}

    monkeypatch.setattr("virusforge.modules.v03_polish_qc.safe_run", lambda cmd, log: None)  # QUAST no-op

    def fake_redirect(cmd, out_path, log_path=None):
        # samtools depth -a → ref pos depth (5 pozisyon, 4 kapsanmış)
        Path(out_path).write_text("NC\t1\t10\nNC\t2\t20\nNC\t3\t0\nNC\t4\t30\nNC\t5\t40\n")
    monkeypatch.setattr(util, "run_redirect", fake_redirect)

    V03PolishQC().run(ctx)
    m = ctx.results["V03"]
    assert "coverage" in m and m["coverage"]["breadth_pct"] == 80.0
    assert "checkv" not in m                              # RNA'da CheckV (faj-odaklı) çalışmaz
