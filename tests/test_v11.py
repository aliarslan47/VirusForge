"""V11 varyant çağırma: RNA+BAM → varyantlar; DNA veya BAM-yok → NOT_APPLICABLE."""
from pathlib import Path

from virusforge.module import Context, Status
from virusforge.modules.v11_variants import V11VariantCall
from virusforge import util


def _ctx(tmp_path, molecule="rna", with_bam=True):
    run = tmp_path / "run"
    run.mkdir(exist_ok=True)
    ref = tmp_path / "ref.fa"
    ref.write_text(">NC\nACGT\n")
    ctx = Context(sample_dir=tmp_path, run_dir=run,
                  cfg={"general": {"molecule": molecule},
                       "tools": {"rna": {"conda_env": "vf_rna"}, "lofreq": {"conda_env": "vf_lofreq"}}},
                  mode="SHORT_READ")
    if with_bam:
        bam = tmp_path / "aln.bam"
        bam.write_text("bam")
        ctx.artifacts["V02"] = {"bam": str(bam), "reference": str(ref)}
    return ctx


def test_v11_na_on_dna(tmp_path):
    res = V11VariantCall().run(_ctx(tmp_path, molecule="dna"))
    assert res.status == Status.NOT_APPLICABLE


def test_v11_na_when_no_bam(tmp_path):
    res = V11VariantCall().run(_ctx(tmp_path, with_bam=False))
    assert res.status == Status.NOT_APPLICABLE


def test_v11_calls_variants_on_rna(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path)

    def fake_pipe(c1, c2, out_path, log_path=None):
        pfx = c2[c2.index("-p") + 1]                    # ivar variants -p <prefix> → <prefix>.tsv
        Path(str(pfx) + ".tsv").write_text(
            "REGION\tPOS\tREF\tALT\tALT_FREQ\tTOTAL_DP\tREF_AA\tALT_AA\n"
            "NC\t241\tC\tT\t0.99\t1000\t\t\n"
            "NC\t23403\tA\tG\t0.15\t900\tD\tG\n")
        open(out_path, "w").write("")

    def fake_safe_run(cmd, log):                         # lofreq → vcf üret
        vcf = cmd[cmd.index("-o") + 1]
        Path(vcf).write_text("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
                             "NC\t241\t.\tC\tT\t5000\tPASS\tDP=1000;AF=0.99\n")
        return None
    monkeypatch.setattr(util, "run_pipe", fake_pipe)
    monkeypatch.setattr("virusforge.modules.v11_variants.safe_run", fake_safe_run)

    res = V11VariantCall().run(ctx)
    m = ctx.results["V11"]
    assert res.status == Status.PASS
    assert m["n_total"] == 2 and m["n_consensus"] == 1 and m["n_minor"] == 1 and m["quasispecies"] is True
    assert len(m["lofreq_variants"]) == 1
