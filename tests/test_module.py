import json

from virusforge.module import STANDARD_DIRS, Context, Module, Status, is_rna


class _Dummy(Module):
    name = "Dummy"
    code = "V99"
    dirname = "V99_DUMMY"


def test_status_enum_values():
    assert {s.value for s in Status} == {
        "PASS", "WARNING", "FAIL", "NOT_APPLICABLE", "SKIPPED"}


def test_make_dirs_creates_8_folders(tmp_path):
    dirs = _Dummy().make_dirs(tmp_path)
    assert len(dirs) == 8
    for d in STANDARD_DIRS:
        assert (tmp_path / "V99_DUMMY" / d).is_dir()


def _ctx(cfg=None, v04=None):
    c = Context(sample_dir=".", run_dir=".", cfg=cfg or {})
    if v04 is not None:
        c.results["V04"] = v04
    return c


def test_is_rna_config_override_is_authoritative():
    # override V04'ten önce bile (V02 assembly için) çalışır
    assert is_rna(_ctx(cfg={"general": {"molecule": "rna"}})) is True
    assert is_rna(_ctx(cfg={"general": {"molecule": "dna"}}, v04={"taxonomy": "Riboviria;..."})) is False


def test_is_rna_auto_from_genomad_riboviria():
    assert is_rna(_ctx(v04={"taxonomy": "Viruses;Riboviria;Orthornavirae;Nidovirales"})) is True
    assert is_rna(_ctx(v04={"taxonomy": "Viruses;Duplodnaviria;Caudoviricetes"})) is False


def test_is_rna_default_dna_when_unknown():
    assert is_rna(_ctx()) is False                       # V04 yok, override yok → DNA varsayılan


def test_write_summary_json_has_status_and_provenance(tmp_path):
    m = _Dummy()
    out = m.write_summary(tmp_path, Status.WARNING, {"x": 1},
                          [{"tool": "t"}])
    data = json.loads(out.read_text())
    assert data["status"] == "WARNING"
    assert data["code"] == "V99"
    assert data["provenance"] == [{"tool": "t"}]
    assert m.is_done(tmp_path)
