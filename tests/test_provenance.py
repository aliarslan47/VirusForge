from virusforge import provenance


def test_record_has_all_fields():
    rec = provenance.record(
        module="V04", tool="genomad", version="1.11.0",
        database="genomad_db", database_version="1.7",
        command="genomad end-to-end ...", params={"threads": 8},
        input_sha256="abc", output_sha256="def",
    )
    for f in ("module", "tool", "version", "database", "database_version",
              "command", "params", "input_sha256", "output_sha256", "timestamp"):
        assert f in rec
    assert rec["tool"] == "genomad"


def test_write_creates_json(tmp_path):
    out = provenance.write(tmp_path, [provenance.record("V00", "detect")])
    assert out.exists() and out.name == "provenance.json"
