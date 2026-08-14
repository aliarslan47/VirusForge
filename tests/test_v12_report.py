"""V12 rapor modülü — çift-dilli çıktı (report.html tr + report_en.html en)."""
from virusforge.modules.v12_report import V12Report
from virusforge.module import Context


def test_v12_writes_dual_language(tmp_path):
    sample_dir = tmp_path / "T7_hybrid"
    sample_dir.mkdir()
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    ctx = Context(sample_dir=sample_dir, run_dir=run_dir, cfg={}, mode="HYBRID")

    V12Report().run(ctx)

    tr = run_dir / "report.html"
    en = run_dir / "report_en.html"
    assert tr.exists() and "Genel Bakış" in tr.read_text()
    assert en.exists() and "Overview" in en.read_text()
