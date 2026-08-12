from virusforge import config, pipeline
from virusforge.module import Context, Module, ModuleResult, Status
from tests.conftest import write_fastq


def _short_sample(tmp_path):
    s = tmp_path / "sample"
    s.mkdir()
    write_fastq(s / "s_R1.fastq", length=150)
    write_fastq(s / "s_R2.fastq", length=150)
    return s


class DummyA(Module):
    name, code, dirname = "A", "V0A", "V0A_A"

    def run(self, ctx: Context) -> ModuleResult:
        (ctx.run_dir / "order.txt").open("a").write("A")
        return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, {}), {})


class DummyB(Module):
    name, code, dirname = "B", "V0B", "V0B_B"

    def run(self, ctx: Context) -> ModuleResult:
        (ctx.run_dir / "order.txt").open("a").write("B")
        return ModuleResult(Status.PASS, self.write_summary(ctx.run_dir, Status.PASS, {}), {})


class Boom(Module):
    name, code, dirname = "A", "V0A", "V0A_A"  # DummyA ile aynı kimlik

    def run(self, ctx: Context) -> ModuleResult:
        raise RuntimeError("koşmamalıydı")


def test_run_creates_run_dir_and_runs_in_order(tmp_path):
    s = _short_sample(tmp_path)
    rd = pipeline.run(s, tmp_path / "runs", modules=[DummyA, DummyB],
                      clock=lambda: "20260812_000000")
    assert rd.name == "20260812_000000_short_read"
    assert (rd / "order.txt").read_text() == "AB"


def test_resume_skips_completed(tmp_path):
    s = _short_sample(tmp_path)
    out = tmp_path / "runs"
    pipeline.run(s, out, modules=[DummyA], clock=lambda: "20260812_000000")
    # aynı run_dir'e Boom ile tekrar → V0A bitmiş sayılır, Boom KOŞMAZ (yoksa RuntimeError)
    rd = pipeline.run(s, out, modules=[Boom], clock=lambda: "20260812_000000")
    import json
    data = json.loads((rd / "V0A_A" / "V0A_summary.json").read_text())
    assert data["status"] == "PASS"   # Boom ezmedi


def test_mode_reflected_in_run_dir(tmp_path):
    s = _short_sample(tmp_path)
    cfg = config.load_config()
    rd = pipeline.run(s, tmp_path / "runs", cfg=cfg, modules=[DummyA],
                      clock=lambda: "20260812_010101")
    assert rd.name.endswith("_short_read")
