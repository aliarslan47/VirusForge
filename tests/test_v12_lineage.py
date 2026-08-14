from pathlib import Path

from virusforge import tools, registry
from virusforge.modules.v12_lineage import parse_pangolin, parse_nextclade


def test_pangolin_cmd():
    cmd = tools.pangolin_cmd("cons.fa", "out.csv", threads=4, conda_env="vf_pangolin")
    assert cmd[:4] == ["conda", "run", "-n", "vf_pangolin"]
    assert "pangolin" in cmd
    assert "cons.fa" in cmd
    assert "--outfile" in cmd and "out.csv" in cmd


def test_nextclade_run_cmd():
    cmd = tools.nextclade_run_cmd("cons.fa", "db/sc2", "nc.tsv", conda_env="vf_nextclade")
    assert cmd[:4] == ["conda", "run", "-n", "vf_nextclade"]
    assert "nextclade" in cmd and "run" in cmd
    assert "-D" in cmd and "db/sc2" in cmd
    assert "--output-tsv" in cmd and "nc.tsv" in cmd
    assert "cons.fa" in cmd


def test_registry_has_lineage_tools():
    assert registry.tool("pangolin")["repo"]
    assert registry.tool("nextclade")["repo"]


import types

from virusforge.modules.v12_lineage import V12Lineage
from virusforge.module import Status


def _ctx(tmp_path, molecule="rna", draft=True, pangolin_enabled=False):
    """Minimal sahte Context: run_dir + cfg + artifacts + results."""
    cons = tmp_path / "cons.fa"
    if draft:
        cons.write_text(">sample\n" + "ACGT" * 50 + "\n")
    cfg = {"general": {"molecule": molecule},
           "tools": {"pangolin": {"conda_env": "vf_pangolin",
                                  "enabled": pangolin_enabled},
                     "nextclade": {"conda_env": "vf_nextclade",
                                   "dataset_dir": str(tmp_path / "db")}}}
    return types.SimpleNamespace(
        run_dir=tmp_path, cfg=cfg,
        artifacts={"V02": {"draft": str(cons)} if draft else {}},
        results={},
    )


def test_v12_not_applicable_dna(tmp_path):
    res = V12Lineage().run(_ctx(tmp_path, molecule="dna"))
    assert res.status == Status.NOT_APPLICABLE


def test_v12_not_applicable_no_consensus(tmp_path):
    res = V12Lineage().run(_ctx(tmp_path, molecule="rna", draft=False))
    assert res.status == Status.NOT_APPLICABLE


def _fake_safe_run(calls):
    def _run(cmd, log_path):
        calls.append(cmd)
        if "pangolin" in cmd:
            out = [c for c in cmd if str(c).endswith(".csv")][0]
            Path(out).write_text("taxon,lineage,qc_status\nsample,BA.2.86,pass\n")
        else:
            idx = cmd.index("--output-tsv")
            Path(cmd[idx + 1]).write_text(
                "index\tseqName\tclade\tNextclade_pango\tqc.overallStatus\n0\ts\t23I\tBA.2.86\tgood\n")
        return None
    return _run


def test_v12_runs_both_tools_when_pangolin_enabled(tmp_path, monkeypatch):
    from virusforge.modules import v12_lineage as mod
    calls = []
    (tmp_path / "db").mkdir()  # nextclade dataset dizini var olmalı
    monkeypatch.setattr(mod, "safe_run", _fake_safe_run(calls))
    res = V12Lineage().run(_ctx(tmp_path, molecule="rna", pangolin_enabled=True))
    assert res.status == Status.PASS
    assert res.metrics["pangolin"]["lineage"] == "BA.2.86"
    assert res.metrics["nextclade"]["clade"] == "23I"
    assert len(calls) == 2      # iki araç da çağrıldı


def test_v12_nextclade_only_when_pangolin_disabled(tmp_path, monkeypatch):
    """Varsayılan: pangolin kapalı → yalnız Nextclade çağrılır, temiz PASS (problem yok)."""
    from virusforge.modules import v12_lineage as mod
    calls = []
    (tmp_path / "db").mkdir()
    monkeypatch.setattr(mod, "safe_run", _fake_safe_run(calls))
    res = V12Lineage().run(_ctx(tmp_path, molecule="rna", pangolin_enabled=False))
    assert res.status == Status.PASS
    assert "pangolin" not in res.metrics          # kapalı → hiç çalışmadı
    assert res.metrics["nextclade"]["clade"] == "23I"
    assert "problems" not in res.metrics          # kapalı araç ≠ hata
    assert len(calls) == 1      # yalnız nextclade


def test_v12_in_default_pipeline_order():
    from virusforge.pipeline import DEFAULT_MODULES
    names = [m.__name__ if isinstance(m, type) else type(m).__name__ for m in DEFAULT_MODULES]
    assert "V12Lineage" in names
    assert names.index("V11VariantCall") < names.index("V12Lineage") < names.index("V10Report")


from virusforge.report.render import render_html


def _report_with_v12():
    return {"sample": "CoV2", "mode": "SHORT_READ", "run_id": "r", "modules": [
        {"code": "V12", "status": "PASS", "metrics": {
            "pangolin": {"lineage": "BA.2.86", "qc_status": "pass", "scorpio_call": "",
                         "conflict": "0.0", "note": "", "pango_version": "4.3.1"},
            "nextclade": {"clade": "23I", "nextclade_pango": "BA.2.86", "qc_overall": "good",
                          "total_substitutions": 72, "total_missing": 305,
                          "total_aa_substitutions": 45}}}]}


def test_render_v12_tr():
    html = render_html(_report_with_v12(), lang="tr")
    assert "Soy/Klad" in html or "Soy Hattı" in html
    assert "BA.2.86" in html      # bilimsel terim korunur
    assert "23I" in html


def test_render_v12_en_no_raw_tr():
    html = render_html(_report_with_v12(), lang="en")
    assert "BA.2.86" in html
    assert "Soy/Klad Tayini" not in html       # EN raporda ham TR başlık sızmamalı
    assert "Lineage" in html or "Clade" in html


def test_parse_pangolin(tmp_path):
    csv = tmp_path / "lineage_report.csv"
    csv.write_text(
        "taxon,lineage,conflict,ambiguity_score,scorpio_call,scorpio_support,"
        "scorpio_conflict,scorpio_notes,version,pangolin_version,scorpio_version,"
        "constellation_version,is_designated,qc_status,qc_notes,note\n"
        "sample,BA.2.86,0.0,,Omicron (BA.2-like),0.9,0.0,,PUSHER-v1.25,4.3.1,"
        "0.3.19,v0.1.12,True,pass,,Assigned from designation hash.\n")
    r = parse_pangolin(csv)
    assert r["lineage"] == "BA.2.86"
    assert r["scorpio_call"] == "Omicron (BA.2-like)"
    assert r["qc_status"] == "pass"
    assert r["pango_version"] == "4.3.1"
    assert "designation" in r["note"]


def test_parse_pangolin_missing_columns(tmp_path):
    csv = tmp_path / "min.csv"
    csv.write_text("taxon,lineage,qc_status\nsample,B.1.1.7,pass\n")
    r = parse_pangolin(csv)
    assert r["lineage"] == "B.1.1.7"
    assert r["scorpio_call"] == ""
    assert r["qc_status"] == "pass"


def test_parse_nextclade(tmp_path):
    tsv = tmp_path / "nextclade.tsv"
    tsv.write_text(
        "index\tseqName\tclade\tNextclade_pango\tqc.overallStatus\t"
        "totalSubstitutions\ttotalMissing\ttotalAminoacidSubstitutions\n"
        "0\tsample\t23I\tBA.2.86\tgood\t72\t305\t45\n")
    r = parse_nextclade(tsv)
    assert r["clade"] == "23I"
    assert r["nextclade_pango"] == "BA.2.86"
    assert r["qc_overall"] == "good"
    assert r["total_substitutions"] == 72
    assert r["total_missing"] == 305
    assert r["total_aa_substitutions"] == 45


def test_parse_nextclade_empty(tmp_path):
    tsv = tmp_path / "empty.tsv"
    tsv.write_text("index\tseqName\tclade\n")
    assert parse_nextclade(tsv) == {}
