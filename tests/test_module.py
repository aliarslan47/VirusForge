import json

from virusforge.module import STANDARD_DIRS, Module, Status


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


def test_write_summary_json_has_status_and_provenance(tmp_path):
    m = _Dummy()
    out = m.write_summary(tmp_path, Status.WARNING, {"x": 1},
                          [{"tool": "t"}])
    data = json.loads(out.read_text())
    assert data["status"] == "WARNING"
    assert data["code"] == "V99"
    assert data["provenance"] == [{"tool": "t"}]
    assert m.is_done(tmp_path)
