"""Uçtan-uca dry-run: harici araçlar mock'lu; tüm modüller sırayla koşup summary yazar.
Gerçek araçlı smoke, kullanıcının vereceği örnekle ayrıca yapılacak."""
import subprocess

from virusforge import config, pipeline, util
from tests.conftest import write_fastq

_CORE = ["V00", "V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V10"]


def test_short_pipeline_runs_all_modules(tmp_path, monkeypatch):
    # harici araç çağrılarını no-op yap
    def fake_run_cmd(cmd, cwd=None, log_path=None):
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def fake_redirect(cmd, out_path, log_path=None):
        open(out_path, "wb").close()

    monkeypatch.setattr(util, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(util, "run_redirect", fake_redirect)

    sample = tmp_path / "sample"
    sample.mkdir()
    write_fastq(sample / "s_R1.fastq", length=150)
    write_fastq(sample / "s_R2.fastq", length=150)

    rd = pipeline.run(sample, tmp_path / "runs", clock=lambda: "20260812_000000")

    # her çekirdek modül summary yazdı mı?
    for code in _CORE:
        matches = list(rd.glob(f"*/{code}_summary.json"))
        assert matches, f"{code} summary yok"
    # rapor üretildi
    assert (rd / "report.html").exists()
    assert (rd / "provenance.json").exists()


def test_rna_pipeline_runs_all_modules(tmp_path, monkeypatch):
    # RNA yolu (molecule=rna + referans): tüm modüller koşar; faj modülleri N/A, V06=VADR
    import json

    def fake_run_cmd(cmd, cwd=None, log_path=None):
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def fake_redirect(cmd, out_path, log_path=None):
        open(out_path, "wb").close()

    def fake_pipe(c1, c2, out_path, log_path=None):
        pfx = c2[c2.index("-p") + 1]                  # ivar consensus -p <prefix> → <prefix>.fa
        open(str(pfx) + ".fa", "w").write(">NC_045512.2\n" + "ACGT" * 20 + "\n")
        open(out_path, "w").write("")

    monkeypatch.setattr(util, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(util, "run_redirect", fake_redirect)
    monkeypatch.setattr(util, "run_pipe", fake_pipe)

    sample = tmp_path / "sample"
    sample.mkdir()
    write_fastq(sample / "cov_R1.fastq", length=150)
    write_fastq(sample / "cov_R2.fastq", length=150)
    ref = tmp_path / "NC_045512.2.fa"
    ref.write_text(">NC_045512.2\n" + "ACGT" * 20 + "\n")
    cfg = config.load_config()
    cfg.setdefault("general", {})["molecule"] = "rna"
    cfg["tools"]["rna"]["reference"] = str(ref)

    rd = pipeline.run(sample, tmp_path / "runs", cfg=cfg, clock=lambda: "20260814_000000")

    for code in _CORE:
        assert list(rd.glob(f"*/{code}_summary.json")), f"{code} summary yok"

    def _status(code):
        f = next(rd.glob(f"*/{code}_summary.json"))
        return json.loads(f.read_text())["status"]

    assert _status("V05") == "NOT_APPLICABLE" and _status("V09") == "NOT_APPLICABLE"
    v06 = json.loads(next(rd.glob("*/V06_summary.json")).read_text())
    assert v06["metrics"].get("annotation") == "VADR"
    assert (rd / "report.html").exists()
