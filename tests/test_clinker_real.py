"""clinker gerçek koşu (ali-clinker env). Env yoksa skip; sessiz mock yok — gerçek HTML üretimi doğrulanır."""
import shutil
import subprocess

import pytest


def _has_clinker_env():
    if not shutil.which("conda"):
        return False
    r = subprocess.run(["conda", "env", "list"], capture_output=True, text=True)
    return "ali-clinker" in r.stdout


# minimal geçerli GenBank: 2 CDS + ORIGIN dizisi (clinker biopython ile parse eder)
_GBK = """LOCUS       {name}                60 bp    DNA     linear   PHG 01-JAN-2020
FEATURES             Location/Qualifiers
     source          1..60
     CDS             1..30
                     /gene="g1"
                     /translation="MKV"
     CDS             31..60
                     /gene="g2"
                     /translation="MTL"
ORIGIN
        1 atgaaagttg gtacgcatgc atgcatgcat atgacgctgt aagcatgcat gcatgcatgc
//
"""


def _mkrun_with_gbk(base, name):
    from tests.test_compare import _mkrun, _add_gbk
    r = _mkrun(base, name)
    _add_gbk(r, _GBK.format(name=name))
    return r


@pytest.mark.skipif(not _has_clinker_env(), reason="ali-clinker env yok")
def test_build_clinker_produces_html(tmp_path):
    from virusforge.compare import build_clinker
    a = _mkrun_with_gbk(tmp_path, "runA")
    b = _mkrun_with_gbk(tmp_path, "runB")
    out = tmp_path / "cmp"
    out.mkdir()
    res = build_clinker([a, b], out, cfg={"general": {"threads": 1},
                                          "tools": {"clinker": {"conda_env": "ali-clinker"}}})
    assert res is not None and res["n_genomes"] == 2
    html = out / res["html"]
    assert html.exists() and html.stat().st_size > 0
    assert "clustermap" in html.read_text().lower()  # portable clustermap.js HTML
