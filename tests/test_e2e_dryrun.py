"""Uçtan-uca dry-run: harici araçlar mock'lu; tüm modüller sırayla koşup summary yazar.
Gerçek araçlı smoke, kullanıcının vereceği örnekle ayrıca yapılacak."""
import subprocess

from virusforge import pipeline, util
from tests.conftest import write_fastq

_CORE = ["V00", "V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09"]


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
