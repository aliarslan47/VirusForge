"""V06 anotasyon: DNA→Pharokka, RNA→VADR dallanması."""
from pathlib import Path

from virusforge.module import Context
from virusforge.modules.v06_annotate import V06Annotate


def test_v06_rna_branch_runs_vadr(tmp_path, monkeypatch):
    genome = tmp_path / "g.fa"
    genome.write_text(">NC\nACGT\n")
    run = tmp_path / "run"
    run.mkdir()
    cfg = {"general": {"molecule": "rna"},
           "tools": {"vadr": {"db": "databases/vadr", "model": "sarscov2", "conda_env": "vf_vadr"}}}
    ctx = Context(sample_dir=tmp_path, run_dir=run, cfg=cfg, mode="SHORT_READ")
    ctx.artifacts["V02"] = {"draft": str(genome)}

    def fake_safe_run(cmd, log):
        out_dir = Path(cmd[-1])              # vadr_cmd son argümanı = çıktı dizini
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{out_dir.name}.vadr.pass.list").write_text("seq1\n")
        (out_dir / f"{out_dir.name}.vadr.fail.list").write_text("")
        (out_dir / f"{out_dir.name}.vadr.alt.list").write_text("#header\n")
        return None
    monkeypatch.setattr("virusforge.modules.v06_annotate.safe_run", fake_safe_run)

    res = V06Annotate().run(ctx)
    m = ctx.results["V06"]
    assert res.status.value == "PASS"
    assert m.get("annotation") == "VADR"
    assert m.get("pass") is True and m.get("n_pass") == 1 and m.get("n_fail") == 0
