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


def test_plot_genome_map_creates_png(tmp_path):
    """gen aralıkları + genom uzunluğu → genome_map.png (RNA gen haritası; matplotlib)."""
    from virusforge.modules.v06_annotate import plot_genome_map
    genes = [("ORF1a", 266, 13468), ("S", 21563, 25384), ("N", 28274, 29533)]
    out = tmp_path / "genome_map.png"
    ok = plot_genome_map(genes, 29903, out, title="SARS-CoV-2", log_path=tmp_path / "log")
    assert ok is True
    assert out.exists() and out.stat().st_size > 0


def test_plot_genome_map_no_genes_is_false(tmp_path):
    from virusforge.modules.v06_annotate import plot_genome_map
    out = tmp_path / "gm.png"
    assert plot_genome_map([], 29903, out, log_path=tmp_path / "log") is False
    assert not out.exists()


def test_render_na_section_shows_reason():
    """N/A modül (içerik yok) boş tablo/'Veri yok' yerine net sebep gösterir; EN'e TR sızmaz."""
    from virusforge.report.render import render_html
    rep = {"sample": "x", "mode": "SHORT_READ", "run_id": "r", "modules": [
        {"code": "V05", "status": "NOT_APPLICABLE", "metrics": {"note": "RNA yolu — Mash faj-özel"}}]}
    tr = render_html(rep, lang="tr")
    assert "uygulanmaz" in tr
    assert "Veri yok" not in tr                    # boş placeholder kalmadı
    en = render_html(rep, lang="en")
    assert "does not apply" in en
    assert "uygulanmaz" not in en                  # ham TR sızmasın (not TR olduğu için gösterilmez)
