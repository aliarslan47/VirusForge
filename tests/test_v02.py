import pytest

from virusforge.modules.v02_assembly import select_assembler

_CFG = {"general": {"threads": 4},
        "tools": {"flye": {"chemistry": "r10"}, "spades": {"careful": True}}}


def test_short_selects_spades(tmp_path):
    cmd, contig = select_assembler("SHORT_READ", {"r1": "a", "r2": "b"}, tmp_path, _CFG)
    assert cmd[0] == "spades.py"
    assert str(contig).endswith("contigs.fasta")


def test_hybrid_selects_unicycler(tmp_path):
    cmd, _ = select_assembler("HYBRID", {"r1": "a", "r2": "b", "long": "l"}, tmp_path, _CFG)
    assert cmd[0] == "unicycler"


def test_long_selects_flye_with_chem(tmp_path):
    cmd, _ = select_assembler("LONG_READ", {"long": "l"}, tmp_path, _CFG)
    assert cmd[0] == "flye" and "--nano-hq" in cmd


def test_missing_long_raises(tmp_path):
    with pytest.raises(ValueError):
        select_assembler("LONG_READ", {"r1": "a"}, tmp_path, _CFG)


def test_rna_short_no_ref_selects_rnaviralspades(tmp_path):
    cfg = {"general": {"threads": 4, "molecule": "rna"}, "tools": {"rna": {"reference": ""}}}
    cmd, contig = select_assembler("SHORT_READ", {"r1": "a", "r2": "b"}, tmp_path, cfg)
    assert cmd[0] == "spades.py" and "--rnaviral" in cmd
    assert str(contig).endswith("contigs.fasta")


def test_rna_reference_consensus_publishes_bam(tmp_path, monkeypatch):
    # Referans-tabanlı RNA yolu: minimap2→sort→(mpileup|ivar consensus)→draft + BAM artifact
    from virusforge.modules.v02_assembly import V02Assembly
    from virusforge.module import Context
    from virusforge import util
    ref = tmp_path / "ref.fa"; ref.write_text(">NC\nACGT\n")
    (tmp_path / "s_R1.fastq").write_text("@r\nACGT\n+\nIIII\n")
    (tmp_path / "s_R2.fastq").write_text("@r\nACGT\n+\nIIII\n")
    cfg = {"general": {"threads": 2, "molecule": "rna"},
           "tools": {"rna": {"reference": str(ref), "conda_env": "vf_rna"}}}
    ctx = Context(sample_dir=tmp_path, run_dir=tmp_path / "run", cfg=cfg, mode="SHORT_READ")
    (tmp_path / "run").mkdir()

    # araçları no-op'la; beklenen çıktı dosyalarını üret
    def fake_redirect(cmd, out_path, log_path=None):
        open(out_path, "w").write("sam")             # minimap2 → sam
    def fake_run(cmd, log_path=None):
        # samtools sort → bam dosyası oluştur
        for i, a in enumerate(cmd):
            if a == "-o":
                open(cmd[i + 1], "w").write("bam")
        return None
    def fake_pipe(c1, c2, out_path, log_path=None):
        # ivar consensus -p <prefix> → <prefix>.fa üretir
        pfx = c2[c2.index("-p") + 1]
        open(str(pfx) + ".fa", "w").write(">NC\nACGT\n")
        open(out_path, "w").write("")
    monkeypatch.setattr(util, "run_redirect", fake_redirect)
    monkeypatch.setattr("virusforge.modules.v02_assembly.safe_run", lambda cmd, log: fake_run(cmd, log))
    monkeypatch.setattr(util, "run_pipe", fake_pipe)

    res = V02Assembly().run(ctx)
    art = ctx.artifacts.get("V02", {})
    assert res.status.value == "PASS"
    assert art.get("draft") and art.get("bam") and art.get("reference") == str(ref)
    assert "consensus" in (ctx.results["V02"].get("assembler", "").lower() or "")
