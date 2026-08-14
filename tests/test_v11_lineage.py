import types
from pathlib import Path

from virusforge import tools, registry
from virusforge.module import Status
from virusforge.modules.v11_lineage import V11Lineage, parse_nextclade
from virusforge.report.render import render_html


def test_nextclade_run_cmd():
    cmd = tools.nextclade_run_cmd("cons.fa", "db/sc2", "nc.tsv", conda_env="vf_nextclade")
    assert cmd[:4] == ["conda", "run", "-n", "vf_nextclade"]
    assert "nextclade" in cmd and "run" in cmd
    assert "-D" in cmd and "db/sc2" in cmd
    assert "--output-tsv" in cmd and "nc.tsv" in cmd
    assert "cons.fa" in cmd


def test_registry_has_nextclade():
    assert registry.tool("nextclade")["repo"]


def test_parse_nextclade(tmp_path):
    tsv = tmp_path / "nextclade.tsv"
    tsv.write_text(
        "index\tseqName\tclade\tNextclade_pango\tqc.overallStatus\t"
        "totalSubstitutions\ttotalMissing\ttotalAminoacidSubstitutions\n"
        "0\tsample\t23I\tBA.2.86\tgood\t72\t305\t45\n")
    r = parse_nextclade(tsv)
    assert r["clade"] == "23I"
    assert r["nextclade_pango"] == "BA.2.86"      # Nextclade PANGO soyunu verir (pangolin gereksiz)
    assert r["qc_overall"] == "good"
    assert r["total_substitutions"] == 72
    assert r["total_missing"] == 305
    assert r["total_aa_substitutions"] == 45


def test_parse_nextclade_empty(tmp_path):
    tsv = tmp_path / "empty.tsv"
    tsv.write_text("index\tseqName\tclade\n")
    assert parse_nextclade(tsv) == {}


def _ctx(tmp_path, molecule="rna", draft=True):
    """Minimal sahte Context: run_dir + cfg + artifacts + results."""
    cons = tmp_path / "cons.fa"
    if draft:
        cons.write_text(">sample\n" + "ACGT" * 50 + "\n")
    cfg = {"general": {"molecule": molecule},
           "tools": {"nextclade": {"conda_env": "vf_nextclade",
                                   "dataset_dir": str(tmp_path / "db")}}}
    return types.SimpleNamespace(
        run_dir=tmp_path, cfg=cfg,
        artifacts={"V02": {"draft": str(cons)} if draft else {}},
        results={},
    )


def test_v11_dirname_is_set():
    assert V11Lineage().dirname == "V11_LINEAGE"
    assert V11Lineage().code == "V11"


def test_v11_not_applicable_dna(tmp_path):
    res = V11Lineage().run(_ctx(tmp_path, molecule="dna"))
    assert res.status == Status.NOT_APPLICABLE


def test_v11_not_applicable_no_consensus(tmp_path):
    res = V11Lineage().run(_ctx(tmp_path, molecule="rna", draft=False))
    assert res.status == Status.NOT_APPLICABLE


def _fake_nextclade(calls):
    def _run(cmd, log_path):
        calls.append(cmd)
        idx = cmd.index("--output-tsv")
        Path(cmd[idx + 1]).write_text(
            "index\tseqName\tclade\tNextclade_pango\tqc.overallStatus\n0\ts\t23I\tBA.2.86\tgood\n")
        return None
    return _run


def test_v11_nextclade_runs(tmp_path, monkeypatch):
    """RNA + konsensüs → Nextclade çağrılır, temiz PASS."""
    from virusforge.modules import v11_lineage as mod
    calls = []
    (tmp_path / "db").mkdir()               # nextclade dataset dizini var olmalı
    monkeypatch.setattr(mod, "safe_run", _fake_nextclade(calls))
    res = V11Lineage().run(_ctx(tmp_path, molecule="rna"))
    assert res.status == Status.PASS
    assert res.metrics["nextclade"]["clade"] == "23I"
    assert "problems" not in res.metrics
    assert len(calls) == 1                  # yalnız nextclade (pangolin yok)


def test_v11_in_default_pipeline_order():
    from virusforge.pipeline import DEFAULT_MODULES
    names = [m.__name__ if isinstance(m, type) else type(m).__name__ for m in DEFAULT_MODULES]
    assert "V11Lineage" in names
    assert names.index("V10VariantCall") < names.index("V11Lineage") < names.index("V12Report")


def _report_with_v11():
    return {"sample": "CoV2", "mode": "SHORT_READ", "run_id": "r", "modules": [
        {"code": "V11", "status": "PASS", "metrics": {
            "nextclade": {"clade": "23I", "nextclade_pango": "BA.2.86", "qc_overall": "good",
                          "total_substitutions": 72, "total_missing": 305,
                          "total_aa_substitutions": 45}}}]}


def test_render_v11_tr():
    html = render_html(_report_with_v11(), lang="tr")
    assert "Soy/Klad" in html or "Soy Hattı" in html
    assert "BA.2.86" in html      # bilimsel terim korunur
    assert "23I" in html
    assert "Pangolin" not in html  # pangolin tamamen kaldırıldı


def test_render_v11_en_no_raw_tr():
    html = render_html(_report_with_v11(), lang="en")
    assert "BA.2.86" in html
    assert "Soy/Klad Tayini" not in html       # EN raporda ham TR başlık sızmamalı
    assert "Lineage" in html or "Clade" in html
